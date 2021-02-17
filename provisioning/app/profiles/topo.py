import os
import logging

from typing import Dict, Final

from app.common.bbox import BBOX
from app.common.util import get_result_path
from app.profiles.common.result import add_or_update
from app.profiles.common.sources import (
    canvec,
    bc_topo,
    bc_hillshade,
    bc_resource_roads,
    trails,
    shelters,
)
from app.profiles.common.tilemill import generate_tiles
from app.common.xyz import transparent_clip_to_bbox, get_edge_tiles


NAME: Final = "topo"
ZOOM_MIN: Final = 0
ZOOM_MAX: Final = 15
OUTPUT_FORMAT: Final = "png"


# scales taken from https://www.maptiler.com/google-maps-coordinates-tile-bounds-projection/
def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    layers = (
        canvec(
            bbox,
            run_id,
            (9244667, 4622334, 2311167, 1155583, 577792, 288896, 144448, 72224, 36112),
        )
        + bc_topo(bbox, run_id)
        + bc_hillshade(bbox, run_id)
        + bc_resource_roads(bbox, run_id)
        + trails(bbox, run_id)
        + shelters(bbox, run_id)
    )
    generate_result = generate_tiles(
        layers, ["common", "topo"], bbox, NAME, ZOOM_MIN, ZOOM_MAX, run_id
    )
    transparent_clip_to_bbox(
        [
            os.path.join(generate_result.tile_dir, tile_path)
            for tile_path in get_edge_tiles(generate_result.tile_dir)
        ],
        bbox,
    )
    logging.info("Transferring generated tile set to result directory")
    add_or_update(generate_result.tile_dir, get_result_path((NAME,)))
