import os
import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from gdal import UseExceptions, ConfigurePythonLogging

from api.extensions.static_files_404_behaviour import StaticFiles404Behaviour
from api.routes.export import router as router_export
from api.routes.files import router as router_files
from api.routes.tile import router as router_tile
from api.routes.upload import router as router_upload
from api.settings import (
    FILES_PATH,
    FILES_DIR,
    UPLOADS_PATH,
    UPLOADS_DIR,
    TILES_PATH,
    TILES_DIR,
    UI_DIR,
    UI_PATH,
    API_LOG_DIR,
)
from api.tile_404.tile_404_handler import tile_404_handler

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

app.mount(UPLOADS_PATH, StaticFiles(directory=UPLOADS_DIR), name="upload")
app.mount(
    TILES_PATH,
    StaticFiles404Behaviour(directory=TILES_DIR, handler_404=tile_404_handler),
    name="tile",
)
app.mount(UI_PATH, StaticFiles(directory=UI_DIR, html=True), name="viewer")
app.mount(FILES_PATH, StaticFiles(directory=FILES_DIR), name="file")


@app.get("/")
async def root():
    return RedirectResponse(f"{UI_PATH}")


def configure_logging():
    requestedLogLevel = os.environ.get("LOG_LEVEL", "info")
    logLevelMapping = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARN,
        "error": logging.ERROR,
    }
    handlers = [
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler(
            filename=os.path.join(API_LOG_DIR, f"api-{os.getpid()}.log"), mode="w"
        ),
    ]
    logging.basicConfig(
        handlers=handlers,
        level=logLevelMapping.get(requestedLogLevel, logging.INFO),
        format="%(levelname)s %(asctime)s %(message)s",
    )

    logger_name = "gdal"
    enable_debug = logging.getLogger().level == logging.DEBUG
    ConfigurePythonLogging(logger_name, enable_debug)
    if not enable_debug:
        # suppress noisy GDAL log output as it is meaningless to most users
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    UseExceptions()


configure_logging()

# Development / debug support, not executed when running in container
# Start a local server on port 8888 by default, or whichever port was provided by the caller, when script / module executed directly
if __name__ == "__main__":

    import uvicorn

    port = 8888 if len(sys.argv) == 1 else int(sys.argv[1])
    logging.info("Available on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
