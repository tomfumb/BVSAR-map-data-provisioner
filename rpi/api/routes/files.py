from uuid import uuid4
import os
from typing import Dict

from fastapi.routing import APIRouter

from api.settings import FILES_DIR, FILES_PATH

router = APIRouter()
ID_KEY = "id"
DIRS_KEY = "dirs"
FILES_KEY = "files"


@router.get("/list")
async def get_file_list():
    return path_to_dict(FILES_DIR, _empty_dict())


# adapted from https://stackoverflow.com/a/46415935/519575
def path_to_dict(path: os.PathLike, builder: Dict[str, object]):
    name = os.path.basename(path)
    if os.path.isdir(path):
        if name not in builder[DIRS_KEY]:
            builder[DIRS_KEY][name] = _empty_dict()
        for nested in os.listdir(path):
            path_to_dict(os.path.join(path, nested), builder[DIRS_KEY][name])
    else:
        builder[FILES_KEY].append(
            {
                "name": name,
                "path": f"{FILES_PATH}/{path.replace(f'{FILES_DIR}/', '')}",
                "size": os.stat(path).st_size,
            }
        )
    return builder


def _empty_dict():
    return {ID_KEY: str(uuid4()), DIRS_KEY: {}, FILES_KEY: []}
