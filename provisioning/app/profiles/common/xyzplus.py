import os
import logging

from typing import Final, List
from shutil import copyfile

from app.common.bbox import BBOX
from app.common.util import get_result_path
from app.common.xyz import merge_tiles, get_edge_tiles
from app.tilemill.ProjectLayer import ProjectLayer
from app.profiles.common.tilemill import generate_tiles
from app.sources.xyz_service import provision as xyz_provisioner
from app.profiles.common.result import add_or_update
from app.common.xyz import transparent_clip_to_bbox


ZOOM_MIN: Final = 0
ZOOM_MAX: Final = 17
OUTPUT_FORMAT: Final = "png"


def execute(
    bbox: BBOX,
    run_id: str,
    xyz_url: str,
    profile_name: str,
    layers: List[ProjectLayer],
    extra_styles: List[str] = list(),
) -> None:
    xyz_result = xyz_provisioner(
        bbox, xyz_url, ZOOM_MIN, ZOOM_MAX, ["image/png", "image/jpeg"], OUTPUT_FORMAT
    )
    generate_result = generate_tiles(
        layers,
        ["common", profile_name] + extra_styles,
        bbox,
        profile_name,
        ZOOM_MIN,
        ZOOM_MAX,
        run_id,
    )
    xyz_tiles_merged = list()
    logging.info(
        f"Merging {len(generate_result.tile_paths)} generated tile(s) to xyz base"
    )
    path_tuples = [
        (
            data_tile.replace(generate_result.tile_dir, xyz_result.tile_dir),
            data_tile,
            data_tile,
        )
        for data_tile in generate_result.tile_paths
    ]
    merge_tiles(path_tuples)
    xyz_tiles_merged = [path_tuple[0] for path_tuple in path_tuples]
    logging.info("Collecting non-generated xyz tiles")
    for xyz_tile in xyz_result.tile_paths:
        if xyz_tile not in xyz_tiles_merged:
            xyz_copy_path = xyz_tile.replace(
                xyz_result.tile_dir, generate_result.tile_dir
            )
            os.makedirs(os.path.dirname(xyz_copy_path), exist_ok=True)
            copyfile(xyz_tile, xyz_copy_path)
    transparent_clip_to_bbox(
        [
            os.path.join(generate_result.tile_dir, tile_path)
            for tile_path in get_edge_tiles(generate_result.tile_dir)
        ],
        bbox,
    )
    logging.info("Transferring combined tile set to result directory")
    add_or_update(generate_result.tile_dir, get_result_path((profile_name,)))
