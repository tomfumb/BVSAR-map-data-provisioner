from typing import Dict

from app.common.BBOX import BBOX
from app.profiles.common.xyzplus import execute as xyzplus_execute, ZOOM_MAX, ZOOM_MIN, OUTPUT_FORMAT
from app.profiles.common.sources import canvec, bc_topo, bc_hillshade, bc_resource_roads, trails, shelters, bc_ates_zones, bc_ates_avpaths, bc_ates_dec_points, bc_ates_poi


NAME = "xyzwinter"

def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    xyzplus_execute(
        bbox,
        run_id,
        args["xyz_url"],
        NAME,
        bc_resource_roads(bbox, run_id) + trails(bbox, run_id) + shelters(bbox, run_id) + bc_ates_zones(bbox, run_id) + bc_ates_avpaths(bbox, run_id) + bc_ates_poi(bbox, run_id) + bc_ates_dec_points(bbox, run_id)
    )
