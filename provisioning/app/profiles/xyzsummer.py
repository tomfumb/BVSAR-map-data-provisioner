import os
import glob

from typing import Dict, Final, List, Tuple

from app.common.BBOX import BBOX
from app.profiles.Profile import Profile
from app.common.util import get_result_path
from app.common.merge_xyz_tiles import merge_xyz_tiles
from app.profiles.common.sources import canvec, bc_topo, bc_hillshade, bc_resource_roads, trails, shelters, bc_wetlands, bc_waterways
from app.tilemill.ProjectLayer import ProjectLayer
from app.profiles.common.tilemill import generate_tiles
from app.sources.xyz_service import provision as xyz_provisioner, get_output_dir as get_output_dir_xyz
from app.profiles.common.result import add_or_update


NAME: Final = "xyzsummer"
ZOOM_MIN: Final = 0
ZOOM_MAX: Final = 17
OUTPUT_FORMAT: Final = "png"

def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    xyz_url = args["xyz_url"]
    xyz_tile_path_base = xyz_provisioner(bbox, xyz_url, ZOOM_MIN, ZOOM_MAX, "image/jpeg", OUTPUT_FORMAT)
    data_layers = bc_resource_roads(bbox, run_id) + trails(bbox, run_id) + shelters(bbox, run_id) + bc_wetlands(bbox, run_id) + bc_waterways(bbox, run_id)
    data_output_dir = generate_tiles(data_layers, ["common", "xyzsummer"], bbox, NAME, ZOOM_MIN, ZOOM_MAX, run_id)
    for data_filename in glob.iglob(os.path.join(data_output_dir, "**", "*.png"), recursive=True):
        xyz_tile_for_data = data_filename.replace(data_output_dir, xyz_tile_path_base)
        merge_xyz_tiles(xyz_tile_for_data, data_filename, data_filename)
    add_or_update(data_output_dir, get_result_path((NAME,)))
