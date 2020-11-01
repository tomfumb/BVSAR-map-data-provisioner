import os

from fastapi.routing import APIRouter

from api.settings import TILES_DIR

router = APIRouter()


@router.get("/list")
async def tile_info():
    tilesets = list()
    for dirname in os.listdir(TILES_DIR):
        profile_path = os.path.join(TILES_DIR, dirname)
        if os.path.isdir(profile_path):
            zooms = sorted(
                [
                    int(zoomdir)
                    for zoomdir in os.listdir(profile_path)
                    if os.path.isdir(os.path.join(profile_path, zoomdir))
                ]
            )
            tilesets.append(
                {"name": dirname, "zoom_min": zooms[0], "zoom_max": zooms[-1],}
            )
    return tilesets
