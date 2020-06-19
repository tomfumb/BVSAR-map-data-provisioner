import requests
import logging
import xml.etree.ElementTree as ET
import ogr
import math
import os
import re

from gdal import Open, Translate, GA_ReadOnly
from pydantic import BaseModel
from pyproj import Transformer, CRS
from typing import Dict, Final, List, Tuple

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.file import skip_file_creation, remove_intermediaries
from provisioning.app.common.httpRetriever import httpRetriever, RetrievalRequest
from provisioning.app.tilemill.ProjectLayerType import ProjectLayerType

DEFAULT_WMS_VERSION: Final = "1.1.1"
DEFAULT_DPI: Final = 96
TARGET_FILE_FORMAT: Final = "tif"
OUTPUT_TYPE: Final = ProjectLayerType.RASTER

class WmsProperties(BaseModel):
    max_width: int
    max_height: int

class TileAxisInterval(BaseModel):
    start: float
    end: float

class PartialCoverageTile(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    scale: int
    width: int
    height: int
    wms_url: str = None
    wms_path: str = None
    final_path: str = None

def provision(bbox: BBOX, base_url: str, wms_crs_code: str, layers: Tuple[str], styles: Tuple[str], scales: Tuple[int], image_format: str, directory: str) -> Dict[int, List[str]]:
    wms_properties = _get_wms_properties(base_url)
    grid = _build_grid_for_bbox(bbox, wms_crs_code, scales, wms_properties)
    grid_for_retrieval = _update_grid_for_retrieval(base_url, grid, layers, styles, wms_crs_code, image_format, directory)
    grid_for_missing = _filter_grid_for_missing(grid_for_retrieval)
    requests = _convert_grid_to_requests(grid_for_missing, image_format)
    httpRetriever(requests)
    if image_format != TARGET_FILE_FORMAT:
        _convert_to_tif(grid_for_missing, wms_crs_code)
    return _convert_grid_to_file_list(grid_for_retrieval)

def _get_wms_properties(base_url: str) -> WmsProperties:
    xml = requests.get(f"{base_url}?service=WMS&request=GetCapabilities&version={DEFAULT_WMS_VERSION}").text
    tree = ET.fromstring(xml)
    ns = {"p": "http://www.opengis.net/wms"}
    default_max_dimension = 4096
    max_width_element, max_height_element = tree.find("./p:Service/p:MaxWidth", ns), tree.find("./p:Service/p:MaxHeight", ns)
    if max_width_element == None or max_height_element == None:
       logging.warn("Cannot determine WMS max image width or height, defaulting to %d", default_max_dimension)
    return WmsProperties(
        max_width=int(max_width_element.text) if max_width_element != None else default_max_dimension,
        max_height=int(max_height_element.text) if max_height_element != None else default_max_dimension
    )

def _build_grid_for_bbox(bbox: BBOX, wms_crs_code: str, scales: Tuple[int], wms_properties: WmsProperties) -> List[PartialCoverageTile]:
    bbox_crs = CRS("EPSG:4326")
    wms_crs = CRS(wms_crs_code)
    transformer = Transformer.from_crs(bbox_crs, wms_crs, always_xy = True)
    llx, lly = list(map(lambda ord: math.floor(ord), transformer.transform(bbox.min_x, bbox.min_y)))
    urx, ury = list(map(lambda ord: math.ceil(ord),  transformer.transform(bbox.max_x, bbox.max_y)))
    crs_origin_x, crs_origin_y = transformer.transform(wms_crs.area_of_use.west, wms_crs.area_of_use.south)
    max_image_pixel_width, max_image_pixel_height = wms_properties.max_width, wms_properties.max_height
    partial_coverage_tiles = list()
 
    def build_intervals(origin: float, interval_size: float, bbox_min: float, bbox_max: float) -> List[TileAxisInterval]:
        intervals = list()
        start = origin
        while start + interval_size <= bbox_min:
            start += interval_size
        intervals.append(start)
        end = start
        while end < bbox_max:
            end += interval_size
            intervals.append(end)
        return [TileAxisInterval(start=interval, end=intervals[i + 1]) for i, interval in enumerate(intervals[0:-1])]
        
    for scale in scales:
        max_image_map_unit_width, max_image_map_unit_height = _pixels_to_map_units(max_image_pixel_width, scale, wms_crs), _pixels_to_map_units(max_image_pixel_height, scale, wms_crs)
        # grid_aligned logic introduced to promote reuse of previously-downloaded tiles
        # without grid-alignment we only request exactly what is required to cover the BBOX, however this means
        # existing files that already partially or completely cover the BBOX are very unlikely to be reused, meaning
        # new files are downloaded for the same area and saved with different filenames
        x_intervals = build_intervals(crs_origin_x, max_image_map_unit_width, llx, urx)
        y_intervals = build_intervals(crs_origin_y, max_image_map_unit_height, lly, ury)
        for x_interval in x_intervals:
            for y_interval in y_intervals:
                partial_coverage_tiles.append(PartialCoverageTile(
                    x_min=x_interval.start,
                    y_min=y_interval.start,
                    x_max=x_interval.end,
                    y_max=y_interval.end,
                    scale=scale,
                    width=max_image_pixel_width,
                    height=max_image_pixel_height
                ))
    return partial_coverage_tiles

def _update_grid_for_retrieval(base_url: str, partial_coverage_tiles: List[PartialCoverageTile], layers: Tuple[str], styles: Tuple[str], wms_crs_code: str, image_format: str, directory: str, transparent: bool = False) -> List[PartialCoverageTile]:
    layers_str = ",".join(layers)
    styles_str = ",".join(styles)
    def define_url_and_paths(tile: PartialCoverageTile) -> PartialCoverageTile:
        tile.wms_url = \
            f"{base_url}?" + \
            f"SERVICE=WMS&" + \
            f"VERSION={DEFAULT_WMS_VERSION}&" + \
            f"REQUEST=GetMap&" + \
            f"BBOX={tile.x_min},{tile.y_min},{tile.x_max},{tile.y_max}&" + \
            f"SRS={wms_crs_code}&" + \
            f"WIDTH={tile.width}&HEIGHT={tile.height}&" + \
            f"LAYERS={layers_str}&" + \
            f"STYLES={styles_str}&" + \
            f"FORMAT=image/{image_format}&" + \
            f"DPI={DEFAULT_DPI}&MAP_RESOLUTION={DEFAULT_DPI}&FORMAT_OPTIONS=dpi:{DEFAULT_DPI}&" + \
            f"TRANSPARENT={transparent}"
        path_base = os.path.join(directory, f"{tile.scale}_{DEFAULT_DPI}_{re.sub('[^0-9a-z]', '_', wms_crs_code, flags=re.IGNORECASE)}_{tile.x_min}_{tile.y_min}")
        tile.wms_path = f"{path_base}.{image_format}"
        tile.final_path = f"{path_base}.{TARGET_FILE_FORMAT}"
        return tile
    return list(map(lambda tile: define_url_and_paths(tile), partial_coverage_tiles))

def _filter_grid_for_missing(grid: List[PartialCoverageTile]) -> List[PartialCoverageTile]:
    return list(filter(lambda tile: not skip_file_creation(tile.final_path), grid))

def _convert_grid_to_requests(grid: List[PartialCoverageTile], image_format: str) -> List[RetrievalRequest]:
    return list(map(lambda tile: RetrievalRequest(path=tile.wms_path, url=tile.wms_url, expected_type=f"image/{image_format}"), grid))

def _convert_grid_to_file_list(grid: List[PartialCoverageTile]) -> Dict[int, List[str]]:
    file_list = dict()
    for tile in grid:
        if not tile.scale in file_list:
            file_list[tile.scale] = list()
        file_list[tile.scale].append(tile.final_path)
    return file_list

def _convert_to_tif(partial_coverage_tiles: List[PartialCoverageTile], wms_crs_code: str) -> None:
    for tile in partial_coverage_tiles:
        if os.path.exists(tile.wms_path):
            logging.debug('Converting %s to %s', tile.wms_path, tile.final_path)
            src_file = Open(tile.wms_path, GA_ReadOnly)
            Translate(
                tile.final_path,
                src_file,
                format = 'GTiff',
                noData = None,
                outputSRS = wms_crs_code,
                # Translate expects bounds in format ulX, ulY, lrX, lrY so flip minY and maxY
                outputBounds = (tile.x_min, tile.y_max, tile.x_max, tile.y_min)
            )
            if remove_intermediaries():
                os.remove(tile.wms_path)
        else:
            logging.warn('Expected file %s does not exist', tile.wms_path)


def _map_units_to_pixels(map_units: float, scale: int, map_crs: CRS) -> float:
    return (map_units / scale) / _get_map_units_in_one_inch(map_crs) * DEFAULT_DPI


def _pixels_to_map_units(pixels: float, scale: int, map_crs: CRS) -> float:
    return ((pixels * scale) / DEFAULT_DPI) * _get_map_units_in_one_inch(map_crs)


def _get_map_units_in_one_inch(map_crs) -> float:
    metres_in_one_inch = 0.0254
    map_crs_metre_conversion_factor = map_crs.axis_info[0].unit_conversion_factor
    return metres_in_one_inch * map_crs_metre_conversion_factor
