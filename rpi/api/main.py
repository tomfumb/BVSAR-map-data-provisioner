import datetime
import math
import os
import re

from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


UPLOADS_DIR = os.path.join(os.path.sep, "www", "uploads")
UPLOADS_PATH = "/uploads/files"
TILES_DIR = os.path.join(os.path.sep, "www", "tiles")
TILES_PATH = "/tiles/files"


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http(s)?://localhost(:\d{1,5})?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "BVSAR Map Server API root"}


@app.get("/uploads/list")
async def list_uploads():
    uploads = list()
    for filename in os.listdir(UPLOADS_DIR):
        if os.path.isfile(os.path.join(UPLOADS_DIR, filename)):
            filepath = os.path.join(UPLOADS_DIR, filename)
            fileinfo = os.stat(filepath)
            uploads.append(
                {
                    "filename": filename,
                    "path": f"{UPLOADS_PATH}/{filename}",
                    "bytes": fileinfo.st_size,
                    "uploaded": int(fileinfo.st_ctime * 1000),
                }
            )
    return sorted(uploads, key=lambda upload: upload["uploaded"])


# curl -F "file=@/Users/tc/Desktop/chips.txt" localhost:9000/upload
@app.post("/upload")
async def create_file(file: UploadFile = File(...)):
    filename_parts = file.filename.split(".")
    filename_name = (
        ".".join(filename_parts[0:-1]) if len(filename_parts) > 1 else filename_parts[0]
    )
    filename_suffix = filename_parts[-1] if len(filename_parts) > 1 else "unknown"
    file_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    unique_filename = os.path.join(
        UPLOADS_DIR,
        "{0}_{1}_{2}.{3}".format(
            filename_name,
            file_time,
            re.sub(r"\-", "", str(uuid4()))[0:8],
            filename_suffix,
        ),
    )
    with open(unique_filename, "wb") as file_write:
        for chunk in iter(lambda: file.file.read(10000), b""):
            file_write.write(chunk)
    return {"saved_to": unique_filename}


@app.delete("/uploads/{filename}")
async def delete_file(filename: str):
    filepath = os.path.join(UPLOADS_DIR, filename)
    if os.path.exists(filepath):
        os.unlink(filepath)


@app.get("/tiles/list")
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


@app.get("/export/pdf/{profile}/{zoom}/{x_min}/{y_min}/{x_max}/{y_max}")
async def export_pdf(
    profile: str, zoom: int, x_min: float, y_min: float, x_max: float, y_max: float
):

    # https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
    def lat_lon_to_tile(lat_deg, lon_deg):
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)

    tile_start = lat_lon_to_tile(y_max, x_min)
    tile_end = lat_lon_to_tile(y_min, x_max)

    # return (tile_start, tile_end)

    tile_paths = list()
    for x in range(tile_start[0], tile_end[0]):
        for y in range(tile_start[1], tile_end[1]):
            tile_paths.append(
                os.path.join(TILES_DIR, profile, str(zoom), str(x), f"{y}.png")
            )

    return {
        "required": tile_paths,
        "exist": list(filter(lambda tile_path: os.path.exists(tile_path), tile_paths)),
    }


app.mount(UPLOADS_PATH, StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount(TILES_PATH, StaticFiles(directory=TILES_DIR), name="tiles")