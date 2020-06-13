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
from typing import Final, List, Tuple

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.file import skip_file_creation
from provisioning.app.common.httpRetriever import httpRetriever, RetrievalRequest

DEFAULT_WMS_VERSION: Final = "1.1.1"
DEFAULT_DPI: Final = 96
TARGET_FILE_FORMAT: Final = "tif"

class WmsProperties(BaseModel):
    max_width: int
    max_height: int

class PartialCoverageTile(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float
    scale: int
    width: int
    height: int

    def get_file_name(self):
        return f"{self.scale}_{self.x_min}_{self.y_min}_{self.x_max}_{self.y_max}"

def provision(bbox: BBOX, base_url: str, wms_crs_code: str, layers: Tuple[str], styles: Tuple[str], scales: Tuple[int], image_format: str, directory: str):
    wms_properties = _get_wms_properties(base_url)
    grid = _build_grid_for_bbox(bbox, wms_crs_code, scales, wms_properties)
    requests = _build_retrieval_requests_for_grid(base_url, grid, layers, styles, wms_crs_code, image_format, directory)
    httpRetriever(requests)
    if image_format != TARGET_FILE_FORMAT:
        _convert_to_tif(grid, wms_crs_code, image_format, directory)

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
    transformer = Transformer.from_crs(bbox_crs, wms_crs_code, always_xy = True)
    llx, lly = list(map(lambda ord: math.floor(ord), transformer.transform(bbox.min_x, bbox.min_y)))
    urx, ury = list(map(lambda ord: math.ceil(ord),  transformer.transform(bbox.max_x, bbox.max_y)))
    align_tiles_to_grid = int(os.environ.get("GRID_ALIGNED_WMS", 1)) == 1
    max_image_pixel_width, max_image_pixel_height = wms_properties.max_width, wms_properties.max_height
    partial_coverage_tiles = list()
    for scale in scales:
        max_image_map_unit_width, max_image_map_unit_height = _pixels_to_map_units(max_image_pixel_width, scale, wms_crs), _pixels_to_map_units(max_image_pixel_height, scale, wms_crs)
        # 'grid_aligned' logic introduced to promote reuse of previously-downloaded tiles
        # without grid-alignment we only request exactly what is required to cover the BBOX, however this means
        # existing files that already partially or completely cover the BBOX are very unlikely to be reused, meaning
        # new files are downloaded for the same area and saved with different filenames
        # we align to a grid by default


        # this logic is problematic for some scales. e.g. 250000 generates 6 images but 4 are not required


        llx_for_scale = max_image_map_unit_width * math.floor(llx / max_image_map_unit_width) if align_tiles_to_grid else llx
        lly_for_scale = max_image_map_unit_height * math.floor(lly / max_image_map_unit_height) if align_tiles_to_grid else lly
        urx_for_scale = max_image_map_unit_width * math.ceil(urx / max_image_map_unit_width) if align_tiles_to_grid else urx
        ury_for_scale = max_image_map_unit_height * math.ceil(ury / max_image_map_unit_height) if align_tiles_to_grid else ury
        total_width_map_units = urx_for_scale - llx_for_scale
        total_height_map_units = ury_for_scale - lly_for_scale
        map_width_in_pixels, map_height_in_pixels = _map_units_to_pixels(total_width_map_units, scale, wms_crs), _map_units_to_pixels(total_height_map_units, scale, wms_crs)
        x_image_count, y_image_count = map_width_in_pixels / max_image_pixel_width, map_height_in_pixels / max_image_pixel_height
        grid_col_count, grid_row_count = math.ceil(x_image_count), math.ceil(y_image_count)
        for i in range(grid_col_count):
            pixel_width_this_image = max_image_pixel_width if i < grid_col_count - 1 or grid_col_count == x_image_count or align_tiles_to_grid else map_width_in_pixels % max_image_pixel_width
            startX = llx_for_scale if i == 0 else partial_coverage_tiles[-1].x_max
            endX = startX + (max_image_map_unit_width if pixel_width_this_image == max_image_pixel_width else _pixels_to_map_units(pixel_width_this_image, scale, wms_crs))
            for j in range(grid_row_count):
                pixel_height_this_image = max_image_pixel_height if j < grid_row_count - 1 or grid_row_count == y_image_count or align_tiles_to_grid else map_height_in_pixels % max_image_pixel_height
                startY = lly_for_scale if j == 0 else partial_coverage_tiles[-1].y_max
                endY = startY + (max_image_map_unit_height if pixel_height_this_image == max_image_pixel_height else _pixels_to_map_units(pixel_height_this_image, scale, wms_crs))
                partial_coverage_tiles.append(PartialCoverageTile(
                    x_min=startX,
                    y_min=startY,
                    x_max=endX,
                    y_max=endY,
                    scale=scale,
                    width=pixel_width_this_image,
                    height=pixel_height_this_image
                ))
    return partial_coverage_tiles


def _map_units_to_pixels(map_units: float, scale: int, map_crs: CRS) -> float:
    return (map_units / scale) / _get_map_units_in_one_inch(map_crs) * DEFAULT_DPI


def _pixels_to_map_units(pixels: float, scale: int, map_crs: CRS) -> float:
    return ((pixels * scale) / DEFAULT_DPI) * _get_map_units_in_one_inch(map_crs)


def _get_map_units_in_one_inch(map_crs) -> float:
    metres_in_one_inch = 0.0254
    map_crs_metre_conversion_factor = map_crs.axis_info[0].unit_conversion_factor
    return metres_in_one_inch * map_crs_metre_conversion_factor

def _build_retrieval_requests_for_grid(base_url: str, partial_coverage_tiles: List[PartialCoverageTile], layers: Tuple[str], styles: Tuple[str], wms_crs_code: str, image_format: str, directory: str, transparent: bool = False):
    requests = list()
    layers_str = ",".join(layers)
    styles_str = ",".join(styles)
    for tile in partial_coverage_tiles:
        url = \
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
        requests.append(RetrievalRequest(
            path=os.path.join(
                directory,
                f"{tile.get_file_name()}.{image_format}"
            ),
            url=url,
            expected_type=f"image/{image_format}"
        ))
    return requests

def _convert_to_tif(partial_coverage_tiles: List[PartialCoverageTile], wms_crs_code: str, image_format: str, directory: str) -> None:
    for tile in partial_coverage_tiles:
        src_path = os.path.join(directory, f"{tile.get_file_name()}.{image_format}")
        dst_path = re.sub(r'\.[a-zA-Z0-9]+$', f".tif", src_path)
        if os.path.exists(src_path):
            if skip_file_creation(dst_path):
                logging.debug('Skipping %s as it already exists', dst_path)
            else:
                logging.debug('Converting %s to %s', src_path, dst_path)
                src_file = Open(src_path, GA_ReadOnly)
                Translate(
                    dst_path,
                    src_file,
                    format = 'GTiff',
                    noData = None,
                    outputSRS = wms_crs_code,
                    # Translate expects bounds in format ulX, ulY, lrX, lrY so flip minY and maxY
                    outputBounds = (tile.x_min, tile.y_max, tile.x_max, tile.y_min)
                )
        else:
            logging.warn('Expected file %s does not exist', src_path)
