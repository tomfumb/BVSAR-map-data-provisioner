import logging
import os

from shutil import copyfile
from typing import Dict, Final

from app.common.bbox import BBOX
from app.common.util import get_result_path
from app.sources.xyz_service import provision as xyz_provisioner


NAME: Final = "xyz"
ZOOM_MIN: Final = 0
ZOOM_MAX: Final = 17
OUTPUT_FORMAT: Final = "png"


def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    result_path = get_result_path((NAME,))
    xyz_url = args["xyz_url"]
    xyz_result = xyz_provisioner(
        bbox, xyz_url, ZOOM_MIN, ZOOM_MAX, "image/jpeg", OUTPUT_FORMAT
    )
    logging.info("Copying xyz tiles to result directory")
    for tile_path in xyz_result.tile_paths:
        target_tile_path = tile_path.replace(xyz_result.tile_dir, result_path)
        os.makedirs(os.path.dirname(target_tile_path), exist_ok=True)
        copyfile(tile_path, target_tile_path)
