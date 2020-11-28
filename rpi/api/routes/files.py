import os

from fastapi.routing import APIRouter

from api.settings import FILES_DIR, FILES_PATH

router = APIRouter()


@router.get("/list")
async def get_file_list():
    filesets = dict()
    for dirname in os.listdir(FILES_DIR):
        parent_dir = os.path.join(FILES_DIR, dirname)
        if os.path.isdir(parent_dir):
            files = sorted(
                [
                    "/".join([FILES_PATH, dirname, filename])
                    for filename in os.listdir(parent_dir)
                    if os.path.isfile(os.path.join(parent_dir, filename))
                ]
            )
            if len(files) > 0:
                filesets[parent_dir] = files
    return filesets
