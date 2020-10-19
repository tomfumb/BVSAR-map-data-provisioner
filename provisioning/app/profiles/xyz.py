import logging
import os

from shutil import copyfile
from typing import Dict, Final, List

from app.common.BBOX import BBOX
from app.common.util import silent_delete, get_result_path
from app.sources.xyz_service import provision as xyz_provisioner, get_output_dir as get_output_dir_xyz
from app.profiles.common.result import add_or_update


NAME: Final = "xyz"
ZOOM_MIN: Final = 0
ZOOM_MAX: Final = 17
OUTPUT_FORMAT: Final = "png"

def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    result_path = get_result_path((NAME,))
    xyz_url = args["xyz_url"]
    add_or_update(xyz_provisioner(bbox, xyz_url, ZOOM_MIN, ZOOM_MAX, "image/jpeg", OUTPUT_FORMAT), result_path)
