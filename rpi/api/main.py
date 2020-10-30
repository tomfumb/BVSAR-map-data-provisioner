import datetime
import os
import re

from gdal import Warp, Translate
from shutil import rmtree
from math import floor
from typing import Tuple
from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from api.export.export import bbox_to_xyz, georeference_raster_tile


UPLOADS_DIR = os.environ.get("UPLOADS_DIR", os.path.join(os.path.sep, "www", "uploads"))
UPLOADS_PATH = "/uploads/files"
TILES_DIR = os.environ.get("TILES_DIR", os.path.join(os.path.sep, "www", "tiles"))
TILES_PATH = "/tiles/files"

CURRENT_DIR = os.path.dirname(__file__)
PARENT_TEMP_DIR = os.path.join(CURRENT_DIR, "export", "temp")


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


@app.get("/export/info/{profile}/{zoom}/{x_min}/{y_min}/{x_max}/{y_max}")
async def export_info(
    profile: str, zoom: int, x_min: float, y_min: float, x_max: float, y_max: float
):
    export_tile_bounds = bbox_to_xyz(x_min, x_max, y_min, y_max, zoom)
    export_tile_counts = tile_counts(*export_tile_bounds)
    return {
        "x_tiles": export_tile_counts[0],
        "y_tiles": export_tile_counts[1],
        "sample": f"{TILES_PATH}/{profile}/{zoom}/{export_tile_bounds[0] + floor(export_tile_counts[0] / 2)}/{export_tile_bounds[1] + floor(export_tile_counts[1] / 2)}.png",
    }


@app.get("/export/pdf/{profile}/{zoom}/{x_min}/{y_min}/{x_max}/{y_max}")
async def export_pdf(
    profile: str, zoom: int, x_min: float, y_min: float, x_max: float, y_max: float
):
    x_tile_min, y_tile_min, x_tile_max, y_tile_max = bbox_to_xyz(
        x_min, x_max, y_min, y_max, zoom
    )
    export_temp_dir = os.path.join(PARENT_TEMP_DIR, str(uuid4()))
    os.makedirs(export_temp_dir)
    tifs = list()
    for x in range(x_tile_min, x_tile_max + 1):
        for y in range(y_tile_min, y_tile_max + 1):
            png_path = os.path.join(TILES_DIR, profile, str(zoom), str(x), f"{y}.png")
            if os.path.exists(png_path):
                tif_path = os.path.join(export_temp_dir, f"{zoom}_{x}_{y}.tif")
                georeference_raster_tile(x, y, zoom, png_path, tif_path)
                tifs.append(tif_path)
    if len(tifs) > 0:
        merge_path = os.path.join(export_temp_dir, "merge.tif")
        Warp(
            merge_path,
            tifs,
            outputBounds=(x_min, y_min, x_max, y_max),
            outputBoundsSRS="EPSG:4326",
            dstSRS="EPSG:3857",
            srcNodata=-1,
            dstNodata=-1,
        )
        pdf_path = os.path.join(export_temp_dir, "merge.pdf")
        Translate(pdf_path, merge_path, format="PDF")
        with open(pdf_path, "rb") as pdf_file:
            pdf_data = pdf_file.read()
        rmtree(export_temp_dir)
        return Response(pdf_data, media_type="application/pdf")
    else:
        rmtree(export_temp_dir)
        return None


app.mount(UPLOADS_PATH, StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount(TILES_PATH, StaticFiles(directory=TILES_DIR), name="tiles")


def tile_counts(
    x_tile_min: int, y_tile_min: int, x_tile_max: int, y_tile_max: int
) -> Tuple[int]:
    return ((x_tile_max - x_tile_min) + 1, (y_tile_max - y_tile_min) + 1)


# Development / debug support, not executed when running in container
# Start a local server on port 8888 by default, or whichever port was provided by the caller, when script / module executed directly
if __name__ == "__main__":
    import sys

    import uvicorn

    port = 8888 if len(sys.argv) == 1 else int(sys.argv[1])
    print("Available on port %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
