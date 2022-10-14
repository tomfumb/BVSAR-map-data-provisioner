import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from api.util import configure_logging

from api.data.mbtiles import cache_connections
from api.routes.export import router as router_export
from api.routes.files import router as router_files
from api.routes.tile import router as router_tile
from api.routes.upload import router as router_upload
from api.routes.data import router as router_data
from api.settings import (
    FILES_PATH,
    FILES_DIR,
    UPLOADS_PATH,
    UPLOADS_DIR,
    UI_DIR,
    UI_PATH,
)

configure_logging()
logger = logging.getLogger(__file__)

cache_connections()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http(s)?://localhost(:\d{1,5})?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_export, prefix="/export")
app.include_router(router_tile, prefix="/tile")
app.include_router(router_upload, prefix="/upload")
app.include_router(router_files, prefix="/files")
app.include_router(router_data, prefix="/data")

app.mount(UPLOADS_PATH, StaticFiles(directory=UPLOADS_DIR), name="upload")
app.mount(UI_PATH, StaticFiles(directory=UI_DIR, html=True), name="viewer")
app.mount(FILES_PATH, StaticFiles(directory=FILES_DIR), name="file")


@app.get("/")
async def root():
    return RedirectResponse(f"{UI_PATH}")


# Development / debug support, not executed when running in container
# Start a local server on port 8888 by default, or whichever port was provided by the caller, when script / module executed directly
if __name__ == "__main__":

    import uvicorn

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    logging.info("Available on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
