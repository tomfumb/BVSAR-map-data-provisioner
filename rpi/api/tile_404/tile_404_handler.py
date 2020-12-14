import os

from starlette.responses import FileResponse


def tile_404_handler(path: str) -> FileResponse:
    response = FileResponse(os.path.join(os.path.dirname(__file__), "blank_tile.png"))
    response.headers.append("X-404-tile-response", "true")
    return response
