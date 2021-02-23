import io
from sqlite3 import Connection, connect
import math
import os

from fastapi.routing import APIRouter
from starlette.responses import StreamingResponse, FileResponse

from api.settings import TILES_DIR

router = APIRouter()
connections = dict()
response_404 = FileResponse(
    os.path.join(os.path.dirname(__file__), "..", "tile_404", "blank_tile.png")
)
response_404.headers.append("X-404-tile-response", "true")


@router.get("/list")
async def tile_info():
    tilesets = list()
    for dirname in os.listdir(TILES_DIR):
        profile_path = os.path.join(TILES_DIR, dirname)
        geojson_path = os.path.join(profile_path, "coverage.geojson")
        if os.path.isdir(profile_path) and os.path.exists(geojson_path):
            try:
                mbtiles_connection = get_mbtiles_connection(dirname)
                zoom_min = 0
                zoom_max = mbtiles_connection.execute(
                    "select max(zoom_level) from tiles"
                ).fetchone()[0]
            except FileNotFoundError:
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
            get_mbtiles_connection(profile_name)
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
        print(f"Error retrieving tile {profile_name}/{z}/{x}/{y}: {e}")


def get_mbtiles_connection(profile_name: str) -> Connection:
    if profile_name not in connections:
        mbtiles_path = os.path.join(TILES_DIR, profile_name, f"{profile_name}.mbtiles")
        if not os.path.exists(mbtiles_path):
            raise FileNotFoundError()
        connections[profile_name] = connect(mbtiles_path)
    return connections[profile_name]
