import os
import re
import sys
import json
import gdal
import time
import random
import logging
import datetime
import requests
import uuid

from app.common.BBOX import BBOX
from app.common.util import get_base_path, TILEMILL_DATA_LOCATION
from app.tilemill.ProjectLayer import ProjectLayer
from app.tilemill.ProjectLayerType import ProjectLayerType
from app.tilemill.ProjectCreationProperties import ProjectCreationProperties
from app.tilemill.ProjectProperties import ProjectProperties
from pyproj import CRS, Transformer
from typing import Dict

def create_or_update_project(tilemill_url: str, project_properties: ProjectCreationProperties) -> None:
    token = _generateToken()
    centre = project_properties.bbox.get_centre()
    project = {
        "bounds": project_properties.bbox.as_tuple(),
        "center": (centre[0], centre[1], project_properties.zoom_min),
        "format": "png8",
        "interactivity": False,
        "minzoom": project_properties.zoom_min,
        "maxzoom": project_properties.zoom_max,
        "srs": CRS("EPSG:3857").to_proj4(),
        "Stylesheet": [{ "id": str(i), "data": content } for i, content in enumerate(project_properties.mss)],
        "Layer": list(map(lambda project_layer: _convert_project_layer_to_layer(project_layer), project_properties.layers)),
        "scale": 1,
        "metatile": 2,
        "id": project_properties.name,
        "name": "",
        "description": "",
        "use-default": False,
        "bones.token": token
    }
    requests.put(
        f"{tilemill_url}/api/Project/{project_properties.name}",
        data = json.dumps(project),
        headers = { "Content-Type": "application/json" },
        cookies = { "bones.token": token }
    )

def request_export(tilemill_url: str, project_properties: ProjectProperties) -> str:
    token = _generateToken()
    nowTs = _getNowAsEpochMs()
    export_filename = "{project_name}_{unique_part}.mbtiles".format(project_name = project_properties.name, unique_part = re.sub("[^a-z0-9]", "", str(uuid.uuid4()), flags=re.IGNORECASE))
    exportDefinition = {
        "progress": 0,
        "status": "waiting",
        "format": "mbtiles",
        "project": project_properties.name,
        "id": str(nowTs),
        "zooms": (project_properties.zoom_min, project_properties.zoom_max),
        "metatile": 2,
        "center": (*project_properties.bbox.get_centre(), project_properties.zoom_min),
        "bounds": project_properties.bbox.as_tuple(),
        "static_zoom": project_properties.zoom_min,
        "filename": export_filename,
        "note": "",
        "bbox": project_properties.bbox.as_tuple(),
        "minzoom": project_properties.zoom_min,
        "maxzoom": project_properties.zoom_max,
        "bones.token": token
    }
    requests.put(
        f"{tilemill_url}/api/Export/{nowTs}",
        data = json.dumps(exportDefinition),
        headers = { "Content-Type": "application/json" },
        cookies = { "bones.token": token }
    )
    while True:
        try:
            statuses = requests.get(f"{tilemill_url}/api/Export").json()
            remaining = None
            for status in statuses:
                status_fileame = status["filename"]
                if status_fileame == export_filename:
                    progress = status["progress"]
                    remaining = (status.get("remaining", sys.maxsize) or 0)
                    logging.info(f"Project {project_properties.name} progress {progress * 100}%, remaining: {remaining}ms")
                    if progress > 0 and remaining == 0: # check both as a race condition in tilemill appears to permit 0 remaining when nothing has started yet
                        return export_filename
                    else:
                        time.sleep(min(10, sys.maxsize if remaining == 0 else remaining / 1000))
        except Exception as ex:
            logging.error(f"API rejected request for update or error processing: {ex}")
            break

def _convert_project_layer_to_layer(project_layer: ProjectLayer) -> Dict[str, object]:
    tilemill_path = project_layer.path.replace(get_base_path(), TILEMILL_DATA_LOCATION)
    layer_id = uuid.uuid4().hex
    bbox_calculators = dict()
    bbox_calculators[ProjectLayerType.RASTER.value] = _getExtentFromRaster
    bbox_calculators[ProjectLayerType.LINESTRING.value] = _getExtentFromShp
    bbox_calculators[ProjectLayerType.POINT.value] = _getExtentFromShp
    if project_layer.type.value not in bbox_calculators:
        raise Exception(f"Do not understand {project_layer.type.value}, unable to calculate BBOX")
    layer_bbox = bbox_calculators[project_layer.type.value](project_layer.path, project_layer.crs_code)
    return {
        "geometry": project_layer.type.value,
        "extent": {"minX": layer_bbox.min_x, "minY": layer_bbox.min_y, "maxX": layer_bbox.max_x, "maxY": layer_bbox.max_y},
        "id": layer_id,
        "class": project_layer.style_class,
        "Datasource": { "file": tilemill_path },
        "layer": None,
        "srs-name": project_layer.crs_code,
        "srs": CRS(project_layer.crs_code).to_proj4(),
        "advanced": {},
        "name": layer_id
    }

def _generateToken() -> str:
    characters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXZY0123456789"
    token = ""
    while len(token) < 32:
        token = token + characters[random.randint(0, len(characters) - 1)]
    return token

def _getNowAsEpochMs() -> int:
    return int(datetime.datetime.now().timestamp())

def _getExtentFromRaster(path: str, crs_code: str) -> BBOX:
    image = gdal.Open(path)
    ulx, xres, _, uly, _, yres = image.GetGeoTransform()
    lrx = ulx + (image.RasterXSize * xres)
    lry = uly + (image.RasterYSize * yres)
    destCrs = CRS("EPSG:4326")
    srcCrs = CRS(crs_code)
    transformer = Transformer.from_crs(srcCrs, destCrs, always_xy = True)
    lowerRight = transformer.transform(lrx, lry)
    upperLeft = transformer.transform(ulx, uly)
    return BBOX(min_x=upperLeft[0], min_y=lowerRight[1], max_x=lowerRight[0], max_y=upperLeft[1])

def _getExtentFromShp(path: str, crs_code: str) -> BBOX:
    driver = gdal.ogr.GetDriverByName("ESRI Shapefile")
    shp_datasource = driver.Open(path)
    shp_layer = shp_datasource.GetLayerByIndex(0)
    shp_extent = shp_layer.GetExtent()
    shp_crs = CRS(crs_code)
    bbox_crs = CRS("EPSG:4326")
    transformer = Transformer.from_crs(shp_crs, bbox_crs, always_xy = True)
    llx, lly = transformer.transform(shp_extent[0], shp_extent[2])
    urx, ury = transformer.transform(shp_extent[1], shp_extent[3])
    return BBOX(min_x=llx, min_y=lly, max_x=urx, max_y=ury)
