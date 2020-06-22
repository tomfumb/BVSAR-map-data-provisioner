import os
import re
import math
import logging

from typing import Final

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.file import skip_file_creation
from provisioning.app.common.httpRetriever import httpRetriever, RetrievalRequest
from provisioning.app.util import get_output_path

CACHE_DIR_NAME_BASE = "xyz-"

def provision(bbox: BBOX, url_template: str, zoom_min: int, zoom_max: int, image_format: str, file_extension: str = None) -> str:
    paths = list()
    requests = list()
    image_extension = file_extension if file_extension else image_format.split("/")[1]
    currentZoom = zoom_min
    out_dir_path = get_output_dir(url_template)
    while currentZoom <= zoom_max:
        zoom_directory = os.path.join(out_dir_path, str(currentZoom))
        llTileX, llTileY = _deg_to_num(bbox.min_y, bbox.min_x, currentZoom)
        urTileX, urTileY = _deg_to_num(bbox.max_y, bbox.max_x, currentZoom)
        currentX = llTileX
        while currentX <= urTileX:
            x_directory = os.path.join(zoom_directory, str(currentX))
            currentY = llTileY
            while currentY >= urTileY:
                path = os.path.join(x_directory, f"{currentY}.{image_extension}")
                paths.append(path)
                if not skip_file_creation(path):
                    requests.append(RetrievalRequest(
                        url=url_template.format(z = currentZoom, x = currentX, y = currentY),
                        path=path,
                        expected_type=image_format
                    ))
                currentY -= 1
            currentX += 1
        currentZoom += 1
    logging.info("%d tile(s) required for BBOX. Already have %d, requesting %d", len(paths), len(paths) - len(requests), len(requests))
    httpRetriever(requests)
    return paths

def get_output_dir(url_template: str) -> str:
    dir_name = "{base}{url_part}".format(base = CACHE_DIR_NAME_BASE, url_part = re.sub("[^a-z0-9]", "", url_template, flags=re.IGNORECASE))
    return get_output_path((dir_name,))

# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def _deg_to_num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)
