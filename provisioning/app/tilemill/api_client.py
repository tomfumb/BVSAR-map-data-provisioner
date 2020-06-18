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

from provisioning.app.common.bbox import BBOX
from provisioning.app.util import get_output_path, TILEMILL_DATA_LOCATION
from provisioning.app.tilemill.ProjectLayer import ProjectLayer
from provisioning.app.tilemill.ProjectProperties import ProjectProperties
from pyproj import CRS, Transformer
from typing import Dict

def create_or_update_project(tilemill_url: str, project_properties: ProjectProperties) -> None:
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
        "Stylesheet": ({ "id": "default", "data": project_properties.mss },),
        "Layer": list(map(lambda project_layer: _convert_project_layer_to_layer(project_layer), project_properties.layers)),
        "scale": 1,
        "metatile": 2,
        "id": project_properties.name,
        "name": "",
        "description": "",
        "use-default": False,
        "bones.token": token
    }
    response = requests.put(
        f"{tilemill_url}/api/Project/{project_properties.name}",
        data = json.dumps(project),
        headers = { "Content-Type": "application/json" },
        cookies = { "bones.token": token }
    )

def _convert_project_layer_to_layer(project_layer: ProjectLayer) -> Dict[str, object]:
    tilemill_path = project_layer.path.replace(get_output_path(), TILEMILL_DATA_LOCATION)
    layer_id = uuid.uuid4().hex
    image_bbox = _getExtentFromRaster(project_layer.path, project_layer.crs_code)
    return {
        "geometry": "raster",
        "extent": {"minX": image_bbox.min_x, "minY": image_bbox.min_y, "maxX": image_bbox.max_x, "maxY": image_bbox.max_y},
        "id": layer_id,
        "class": project_layer.style_class,
        "Datasource": { "file": tilemill_path },
        "layer": None,
        "srs-name": project_layer.crs_code,
        "srs": CRS(project_layer.crs_code).to_proj4(),
        "advanced": {},
        "name": layer_id
    }

# def requestExport(userArgs, projectDefinition, projectDirectoryPath, environmentConfig):
#     token = _generateToken()
#     nowTs = _getNowAsEpochMs()
#     projectName = projectDefinition.get("projectName")
#     lowestZoom = projectDefinition.get("lowestZoom")
#     highestZoom = projectDefinition.get("highestZoom")
#     minX, minY, maxX, maxY = userArgs.get("minX"), userArgs.get("minY"), userArgs.get("maxX"), userArgs.get("maxY")
#     centreX, centreY = projectDefinition.get("centreX"), projectDefinition.get("centreY")
#     exportDefinition = {
#         "progress": 0,
#         "status": "waiting",
#         "format": "mbtiles",
#         "project": projectName,
#         "id": projectName,
#         "zooms": (lowestZoom, highestZoom),
#         "metatile": 2,
#         "center": (centreX, centreY, lowestZoom),
#         "bounds": (minX, minY, maxX, maxY),
#         "static_zoom": lowestZoom,
#         "filename": "{projectName}.mbtiles".format(projectName = projectName),
#         "note": "",
#         "bbox": (minX, minY, maxX, maxY),
#         "minzoom": lowestZoom,
#         "maxzoom": highestZoom,
#         "bones.token": token
#     }
#     requests.put(
#         "{url}/api/Export/{nowTs}".format(url = environmentConfig.get("tilemillUrl"), nowTs = nowTs),
#         data = json.dumps(exportDefinition),
#         headers = { "Content-Type": "application/json" },
#         cookies = { "bones.token": token }
#     )
#     isComplete = False
#     while isComplete == False:
#         try:
#             statuses = requests.get("{url}/api/Export".format(url = environmentConfig.get("tilemillUrl"))).json()
#             remaining = None
#             for status in statuses:
#                 statusProject = status.get("project", None)
#                 if statusProject == projectName:
#                     progress = status.get("progress")
#                     remaining = status.get("remaining", sys.maxsize)
#                     logging.debug("Project %s progress %d%%, remaining: %dms", projectName, progress * 100, remaining)
#                     if progress > 0 and remaining == 0: # check both as a race condition in tilemill appears to permit 0 remaining when nothing has started yet
#                         isComplete = True
#                     else:
#                         time.sleep(min(5, sys.maxsize if remaining == 0 else remaining / 1000))
#             if remaining == None:
#                 logging.warn("No status available for current project, something went wrong")
#                 break
#         except Exception as ex:
#             logging.error("API rejected request for update or error processing: %s", str(ex))
#             break
#     logging.info("Export complete")

#     response = requests.get("{url}/export/download/{projectName}.mbtiles".format(url = environmentConfig.get("tilemillUrl"), projectName = projectName))
#     with open(os.path.join(projectDirectoryPath, "output.mbtiles"), "wb") as file:
#         file.write(response.content)
#     logging.info("Finished")

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
