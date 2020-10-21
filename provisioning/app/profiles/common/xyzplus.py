import os
import logging

from typing import Final, List
from shutil import copyfile

from app.common.BBOX import BBOX
from app.common.util import get_result_path
from app.common.merge_xyz_tiles import merge_xyz_tiles
from app.tilemill.ProjectLayer import ProjectLayer
from app.profiles.common.tilemill import generate_tiles
from app.sources.xyz_service import provision as xyz_provisioner
from app.profiles.common.result import add_or_update


ZOOM_MIN: Final = 0
ZOOM_MAX: Final = 17
OUTPUT_FORMAT: Final = "png"


def execute(
    bbox: BBOX, run_id: str, xyz_url: str, profile_name: str, layers: List[ProjectLayer]
) -> None:
    xyz_result = xyz_provisioner(
        bbox, xyz_url, ZOOM_MIN, ZOOM_MAX, "image/jpeg", OUTPUT_FORMAT
    )
    generate_result = generate_tiles(
        layers, ["common", profile_name], bbox, profile_name, ZOOM_MIN, ZOOM_MAX, run_id
    )
    xyz_tiles_merged = list()
    logging.info("Merging generated tiles to xyz base")
    for data_tile in generate_result.tile_paths:
        matching_raw_xyz_tile = data_tile.replace(
            generate_result.tile_dir, xyz_result.tile_dir
        )
        existing_merge_tile = data_tile.replace(
            generate_result.tile_dir, get_result_path((profile_name,))
        )
        merge_xyz_tiles(
            existing_merge_tile
            if os.path.exists(existing_merge_tile)
            else matching_raw_xyz_tile,
            data_tile,
            data_tile,
        )
        xyz_tiles_merged.append(matching_raw_xyz_tile)
    logging.info("Collecting non-generated xyz tiles")
    for xyz_tile in xyz_result.tile_paths:
        if xyz_tile not in xyz_tiles_merged:
            xyz_copy_path = xyz_tile.replace(
                xyz_result.tile_dir, generate_result.tile_dir
            )
            os.makedirs(os.path.dirname(xyz_copy_path), exist_ok=True)
            copyfile(xyz_tile, xyz_copy_path)
    logging.info("Transferring combined tile set to result directory")
    add_or_update(generate_result.tile_dir, get_result_path((profile_name,)))
