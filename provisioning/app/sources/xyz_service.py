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

def provision(bbox: BBOX, url_template: str, image_format: str, zoom_min: int, zoom_max: int) -> str:

    requests = list()
    cache_dir_name = "{base}{url_part}".format(base = CACHE_DIR_NAME_BASE, url_part = re.sub("[^a-z0-9]", "", url_template, flags=re.IGNORECASE))
    image_extension = image_format.split("/")[1]
    currentZoom = zoom_min
    while currentZoom <= zoom_max:
        zoom_directory = get_output_path((cache_dir_name,))
        llTileX, llTileY = deg2num(bbox.min_y, bbox.min_x, currentZoom)
        urTileX, urTileY = deg2num(bbox.max_y, bbox.max_x, currentZoom)
        currentX = llTileX
        while currentX <= urTileX:
            x_directory = os.path.join(zoom_directory, str(currentX))
            currentY = llTileY
            while currentY >= urTileY:
                path = os.path.join(x_directory, f"{currentY}.{image_extension}")
                if not skip_file_creation(path):
                    requests.append(RetrievalRequest(
                        url=url_template.format(z = currentZoom, x = currentX, y = currentY),
                        path=path,
                        expected_type=image_format
                    ))
                currentY -= 1
            currentX += 1
        currentZoom += 1
    httpRetriever(requests)
    return cache_dir_name

# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)
