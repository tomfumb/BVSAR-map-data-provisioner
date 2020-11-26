import os

from fastapi.routing import APIRouter

from api.settings import FILES_DIR, FILES_PATH

router = APIRouter()


@router.get("")
async def get_file_list():
    filesets = dict()
    for dirname in os.listdir(FILES_DIR):
        parent_dir = os.path.join(FILES_DIR, dirname)
        if os.path.isdir(parent_dir):
            filesets[parent_dir] = sorted(
                [
                    "/".join([FILES_PATH, filename])
                    for filename in os.listdir(parent_dir)
                    if os.path.isfile(os.path.join(parent_dir, filename))
                ]
            )
    return filesets
