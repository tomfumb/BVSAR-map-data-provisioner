import os
import re
import math
import logging

from enum import Enum
from pydantic import BaseModel
from pygeotile.tile import Tile
from typing import Dict, Final, List

from app.common.BBOX import BBOX
from app.common.http_retriever import retrieve, ExistsCheckRequest, RetrievalRequest
from app.common.util import get_cache_path, skip_file_creation

CACHE_DIR_NAME_BASE = "xyz-"

class UrlFormat(Enum):
    XYZ = 0
    QUADKEY = 1

class ProvisionResult(BaseModel):
    tile_paths: List[str]
    tile_dir: str

def provision(bbox: BBOX, url_template: str, zoom_min: int, zoom_max: int, image_format: str, file_extension: str = None) -> ProvisionResult:
    tiles = _identify_tiles(bbox, zoom_min, zoom_max)
    retrieve(_build_retrieval_requests(
        tiles,
        url_template,
        image_format,
        file_extension,
    ))
    return ProvisionResult(
        tile_dir=get_output_dir(url_template),
        tile_paths=_build_tile_paths(tiles, url_template, image_format, file_extension)
    )

def build_exists_check_requests(bbox: BBOX, url_template: str, zoom_min: int, zoom_max: int, image_format: str, file_extension: str = None) -> List[ExistsCheckRequest]:
    requests = list()
    url_format = _determine_format(url_template)
    for z, xs in _identify_tiles(bbox, zoom_min, zoom_max).items():
        for x, ys in xs.items():
            for y in ys:
                requests.append(ExistsCheckRequest(
                    url=_build_tile_url(url_format, url_template, z, x, y),
                ))
    return requests

def get_output_dir(url_template: str) -> str:
    dir_name = "{base}{url_part}".format(base = CACHE_DIR_NAME_BASE, url_part = re.sub("[^a-z0-9]", "", url_template, flags=re.IGNORECASE))
    return get_cache_path((dir_name,))

def _identify_tiles(bbox: BBOX, zoom_min: int, zoom_max: int) -> Dict[int, Dict[int, List[int]]]:
    tiles = dict()
    currentZoom = zoom_min
    while currentZoom <= zoom_max:
        tiles[currentZoom] = dict()
        llTileX, llTileY = _deg_to_num(bbox.min_y, bbox.min_x, currentZoom)
        urTileX, urTileY = _deg_to_num(bbox.max_y, bbox.max_x, currentZoom)
        currentX = llTileX
        while currentX <= urTileX:
            tiles[currentZoom][currentX] = list()
            currentY = llTileY
            while currentY >= urTileY:
                tiles[currentZoom][currentX].append(currentY)
                currentY -= 1
            currentX += 1
        currentZoom += 1
    return tiles

def _build_retrieval_requests(tiles: Dict[int, Dict[int, List[int]]], url_template: str, image_format: str, file_extension: str = None) -> List[RetrievalRequest]:
    requests = list()
    url_format = _determine_format(url_template)
    for z, xs in tiles.items():
        for x, ys in xs.items():
            for y in ys:
                path = _build_tile_path(z, x, y, url_template, image_format, file_extension)
                if skip_file_creation(path):
                    continue
                requests.append(RetrievalRequest(
                    url=_build_tile_url(url_format, url_template, z, x, y),
                    path=path,
                    expected_type=image_format,
                ))
    return requests

def _build_tile_paths(tiles: Dict[int, Dict[int, List[int]]], url_template: str, image_format: str, file_extension: str = None) -> List[str]:
    paths = list()
    for z, xs in tiles.items():
        for x, ys in xs.items():
            for y in ys:
                paths.append(_build_tile_path(z, x, y, url_template, image_format, file_extension))
    return paths

def _determine_format(url_template: str) -> UrlFormat:
    if re.search(r"\{q\}", url_template):
        return UrlFormat.QUADKEY
    elif re.search(r"\{z\}", url_template) and re.search(r"\{x\}", url_template) and re.search(r"\{y\}", url_template):
        return UrlFormat.XYZ
    else:
        raise ValueError(f"URL is not an expected format: {url_template}")

def _build_tile_path(z: int, x: int, y: int, url_template: str, image_format: str, file_extension: str = None) -> str:
    out_dir_path = get_output_dir(url_template)
    image_extension = file_extension if file_extension else image_format.split("/")[1]
    x_dir = os.path.join(os.path.join(out_dir_path, str(z)), str(x))
    return os.path.join(x_dir, f"{y}.{image_extension}")

# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def _deg_to_num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def _build_tile_url(url_format: UrlFormat, url_template: str, z: int, x: int, y: int) -> str:
    if url_format == UrlFormat.QUADKEY:
        return url_template.format(q = Tile.from_google(google_x=x, google_y=y, zoom=z).quad_tree)
    if url_format == UrlFormat.XYZ:
        return url_template.format(z = z, x = x, y = y)
