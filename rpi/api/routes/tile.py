from PIL import Image
import logging
from time import time
import io
import json
import math
import os
from threading import Lock
from typing import Optional
from fastapi.routing import APIRouter
from starlette.responses import StreamingResponse, FileResponse
from api.data.mbtiles import get_connection

from api.settings import TILES_DIR

router = APIRouter()
response_404 = FileResponse(
    os.path.join(os.path.dirname(__file__), "..", "tile_404", "blank_tile.png")
)
response_404.headers.append("X-404-tile-response", "true")

tilesets = list()
tilesets_lock = Lock()


@router.get("/list")
async def tile_info():
    with tilesets_lock:
        if len(tilesets) == 0:
            for dirname in os.listdir(TILES_DIR):
                profile_path = os.path.join(TILES_DIR, dirname)
                geojson_path = os.path.join(profile_path, "coverage.geojson")
                attribution_path = os.path.join(profile_path, "attribution.json")
                if os.path.isdir(profile_path) and os.path.exists(geojson_path):
                    mbtiles_connection = get_connection(dirname)
                    if mbtiles_connection:
                        zoom_min = 0
                        zoom_max_start = time()
                        zoom_max = mbtiles_connection.execute(
                            "select max(zoom_level) from tiles"
                        ).fetchone()[0]
                        logging.info(
                            f"{dirname} zoom limits from mbtiles in {time() - zoom_max_start}s"
                        )
                    else:
                        logging.info(
                            f"{dirname} mbtiles not available, falling-back to directory analysis"
                        )
                        zooms = sorted(
                            [
                                int(zoomdir)
                                for zoomdir in os.listdir(profile_path)
                                if os.path.isdir(os.path.join(profile_path, zoomdir))
                            ]
                        )
                        zoom_min = 0
                        zoom_max = zooms[-1]
                    with open(geojson_path) as geojson_file:
                        geojson = "".join(geojson_file.readlines())
                    attribution = None
                    if os.path.exists(attribution_path):
                        with open(attribution_path) as attribution_file:
                            attribution = "".join(attribution_file.readlines())
                    tilesets.append(
                        {
                            "name": dirname,
                            "zoom_min": zoom_min,
                            "zoom_max": zoom_max,
                            "last_modified": math.floor(
                                os.stat(geojson_path).st_mtime * 1000
                            ),
                            "geojson": geojson,
                            "attribution": json.loads(attribution)
                            if attribution is not None
                            else [],
                        }
                    )
    return tilesets


@router.get("/file/{profile_name}/{z}/{x}/{y}.png")
async def tile(
    profile_name: str, z: int, x: int, y: int, supertile: Optional[int] = 0
) -> StreamingResponse:
    tile_bytes = None
    if supertile == 1:
        tile_bytes = get_super_tile(profile_name, z, x, y)
    else:
        tile_bytes = get_tile_bytes(profile_name, z, x, y)
    return (
        StreamingResponse(io.BytesIO(tile_bytes), media_type="image/png")
        if tile_bytes
        else response_404
    )


def get_tile_bytes(profile_name: str, z: int, x: int, y: int) -> bytes:
    mbtiles_connection = get_connection(profile_name)
    try:
        if mbtiles_connection:
            tile_row = mbtiles_connection.execute(
                "select tile_data from tiles where zoom_level = ? and tile_column = ? and tile_row = ?",
                (z, x, y),
            ).fetchone()
            if tile_row is None:
                return None
            return tile_row[0]
        else:
            tile_path = (
                f"{os.path.join(TILES_DIR, profile_name, str(z), str(x), str(y))}.png"
            )
            if os.path.exists(tile_path):
                with open(tile_path, "rb") as f:
                    return f.read()
            return None
    except Exception as e:
        logging.warning(f"Error retrieving tile {profile_name}/{z}/{x}/{y}: {e}")


def get_super_tile(profile_name: str, z: int, x: int, y: int) -> bytes:
    def image_from_bytes(bytes: bytes) -> Image:
        return Image.open(io.BytesIO(bytes)) if bytes else None

    super_zoom = z + 1
    top_left = image_from_bytes(get_tile_bytes(profile_name, super_zoom, x * 2, y * 2))
    top_right = image_from_bytes(
        get_tile_bytes(profile_name, super_zoom, x * 2 + 1, y * 2)
    )
    bottom_left = image_from_bytes(
        get_tile_bytes(profile_name, super_zoom, x * 2, y * 2 + 1)
    )
    bottom_right = image_from_bytes(
        get_tile_bytes(profile_name, super_zoom, x * 2 + 1, y * 2 + 1)
    )
    if top_left or top_right or bottom_left or bottom_right:
        super_tile = Image.new("RGBA", (512, 512))
        if top_left:
            super_tile.paste(top_left, (0, 0))
        if top_right:
            super_tile.paste(top_right, (256, 0))
        if bottom_left:
            super_tile.paste(bottom_left, (0, 256))
        if bottom_right:
            super_tile.paste(bottom_right, (256, 256))
        byte_content = io.BytesIO()
        super_tile.save(byte_content, format="PNG")
        return byte_content.getvalue()
    else:
        return None
