from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.routes.export import router as router_export
from api.routes.status import router as router_status
from api.routes.tile import router as router_tile
from api.routes.upload import router as router_upload
from api.settings import (
    UPLOADS_PATH,
    UPLOADS_DIR,
    TILES_PATH,
    TILES_DIR,
    UI_DIR,
    UI_PATH,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http(s)?://localhost(:\d{1,5})?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router_export, prefix="/export")
app.include_router(router_status, prefix="/status")
app.include_router(router_tile, prefix="/tile")
app.include_router(router_upload, prefix="/upload")

app.mount(UPLOADS_PATH, StaticFiles(directory=UPLOADS_DIR), name="upload")
app.mount(TILES_PATH, StaticFiles(directory=TILES_DIR), name="tile")
app.mount(UI_PATH, StaticFiles(directory=UI_DIR, html=True), name="viewer")


@app.get("/")
async def root():
    return RedirectResponse(f"{UI_PATH}")


# Development / debug support, not executed when running in container
# Start a local server on port 8888 by default, or whichever port was provided by the caller, when script / module executed directly
if __name__ == "__main__":
    import sys

    import uvicorn

    port = 8888 if len(sys.argv) == 1 else int(sys.argv[1])
    print("Available on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
