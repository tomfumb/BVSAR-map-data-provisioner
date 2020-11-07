import logging
import os

from shutil import copyfile
from typing import Dict, Final

from app.common.bbox import BBOX
from app.common.util import get_result_path, get_run_data_path
from app.common.xyz import get_edge_tiles, transparent_clip_to_bbox
from app.profiles.common.result import add_or_update
from app.sources.xyz_service import provision as xyz_provisioner


NAME: Final = "xyz"
ZOOM_MIN: Final = 0
ZOOM_MAX: Final = 17
OUTPUT_FORMAT: Final = "png"


def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    xyz_result = xyz_provisioner(
        bbox, args["xyz_url"], ZOOM_MIN, ZOOM_MAX, "image/jpeg", OUTPUT_FORMAT
    )
    tmp_dir = get_run_data_path(run_id, (NAME,))
    tmp_tile_paths = list()
    logging.info(
        f"Copying {len(xyz_result.tile_paths)} {NAME} tiles to tmp dir for edge clipping"
    )
    for tile_path in xyz_result.tile_paths:
        tmp_tile_path = tile_path.replace(xyz_result.tile_dir, tmp_dir)
        tmp_tile_paths.append(tmp_tile_path)
        os.makedirs(os.path.dirname(tmp_tile_path), exist_ok=True)
        copyfile(tile_path, tmp_tile_path)
    transparent_clip_to_bbox(
        [os.path.join(tmp_dir, tile_path) for tile_path in get_edge_tiles(tmp_dir)],
        bbox,
    )
    add_or_update(tmp_dir, get_result_path((NAME,)))
