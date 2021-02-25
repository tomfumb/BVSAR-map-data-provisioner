import logging
from time import time
import io
import math
import os
from threading import Lock
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
                if os.path.isdir(profile_path) and os.path.exists(geojson_path):
                    try:
                        mbtiles_connection = get_connection(dirname)
                        zoom_min = 0
                        zoom_max_start = time()
                        zoom_max = mbtiles_connection.execute(
                            "select max(zoom_level) from tiles"
                        ).fetchone()[0]
                        logging.info(
                            f"{dirname} zoom limits from mbtiles in {time() - zoom_max_start}s"
                        )
                    except FileNotFoundError:
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
                        tilesets.append(
                            {
                                "name": dirname,
                                "zoom_min": zoom_min,
                                "zoom_max": zoom_max,
                                "last_modified": math.floor(
                                    os.stat(geojson_path).st_mtime * 1000
                                ),
                                "geojson": "".join(geojson_file.readlines()),
                            }
                        )
    return tilesets


@router.get("/file/{profile_name}/{z}/{x}/{y}.png")
async def tile(profile_name: str, z: int, x: int, y: int) -> StreamingResponse:
    try:
        tile_row = (
            get_connection(profile_name)
            .execute(
                "select tile_data from tiles where zoom_level = ? and tile_column = ? and tile_row = ?",
                (z, x, y),
            )
            .fetchone()
        )
        if tile_row is None:
            return response_404
        img_bytes = io.BytesIO(tile_row[0])
        img_bytes.seek(0)
        return StreamingResponse(img_bytes, media_type="image/png")
    except FileNotFoundError:
        tile_path = (
            f"{os.path.join(TILES_DIR, profile_name, str(z), str(x), str(y))}.png"
        )
        if os.path.exists(tile_path):
            return FileResponse(tile_path)
        return response_404
    except Exception as e:
        logging.warning(f"Error retrieving tile {profile_name}/{z}/{x}/{y}: {e}")
