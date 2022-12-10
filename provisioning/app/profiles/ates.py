import os
import logging

from typing import Dict, Final

from app.common.bbox import BBOX
from app.common.util import get_result_path
from app.profiles.common.result import add_or_update
from app.profiles.common.sources import (
    bc_ates_zones,
    bc_ates_avpaths,
    bc_ates_dec_points,
    bc_ates_poi,
)
from app.profiles.common.tilemill import generate_tiles
from app.common.xyz import transparent_clip_to_bbox, get_edge_tiles


NAME: Final = "ates"
ZOOM_MIN: Final = 0
ZOOM_MAX: Final = 17
OUTPUT_FORMAT: Final = "png"


def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    layers = (
        bc_ates_zones(bbox, run_id)
        + bc_ates_avpaths(bbox, run_id)
        + bc_ates_poi(bbox, run_id)
        + bc_ates_dec_points(bbox, run_id)
    )
    generate_result = generate_tiles(
        layers, ["common-winter"], bbox, NAME, ZOOM_MIN, ZOOM_MAX, run_id
    )
    transparent_clip_to_bbox(
        [
            os.path.join(generate_result.tile_dir, tile_path)
            for tile_path in get_edge_tiles(generate_result.tile_dir)
        ],
        bbox,
        False,
    )
    logging.info("Transferring generated tile set to result directory")
    add_or_update(generate_result.tile_dir, get_result_path((NAME,)), False)
