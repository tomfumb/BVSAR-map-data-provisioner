import datetime
import os
import re

from uuid import uuid4

from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles


UPLOADS_DIR = os.path.join(os.path.sep, "www", "uploads")
UPLOADS_PATH = "/uploads/files"
TILES_DIR = os.path.join(os.path.sep, "www", "tiles")
TILES_PATH = "/tiles/files"

app = FastAPI()


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
    tilesets = dict()
    print(f"base_dir: {TILES_DIR}")
    for dirname in os.listdir(TILES_DIR):
        print(f"dirname: {dirname}")
        profile_path = os.path.join(TILES_DIR, dirname)
        print(f"profile_path: {profile_path}")
        if os.path.isdir(profile_path):
            zooms = sorted(
                [
                    int(zoomdir)
                    for zoomdir in os.listdir(profile_path)
                    if os.path.isdir(os.path.join(profile_path, zoomdir))
                ]
            )
            print(f"zooms: {zooms}")
            tilesets[dirname] = {
                "zoom_min": zooms[0],
                "zoom_max": zooms[-1],
            }
    return tilesets


app.mount(UPLOADS_PATH, StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.mount(TILES_PATH, StaticFiles(directory="/www/tiles"), name="tiles")
