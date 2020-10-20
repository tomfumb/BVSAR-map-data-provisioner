import logging
import os

from shutil import copyfile
from typing import Dict, Final, List

from app.common.BBOX import BBOX
from app.common.util import silent_delete, get_result_path
from app.profiles.common.result import add_or_update
from app.profiles.common.sources import canvec, bc_topo, bc_hillshade, bc_resource_roads, trails, shelters
from app.profiles.common.tilemill import generate_tiles
from app.tilemill.ProjectLayer import ProjectLayer


NAME: Final = "topo"
ZOOM_MIN: Final = 0
ZOOM_MAX: Final = 17
OUTPUT_FORMAT: Final = "png"

def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    layers = canvec(bbox, run_id, (10000000, 4000000, 2000000, 1000000, 500000, 250000, 150000, 70000, 35000)) + bc_topo(bbox, run_id) + bc_hillshade(bbox, run_id) + bc_resource_roads(bbox, run_id) + trails(bbox, run_id) + shelters(bbox, run_id)
    tile_output_dir = generate_tiles(layers, ["common", "topo"], bbox, NAME, ZOOM_MIN, ZOOM_MAX, run_id).tile_dir
    logging.info("Transferring generated tile set to result directory")
    add_or_update(tile_output_dir, get_result_path((NAME,)))
