from typing import Dict, Final

from app.common.bbox import BBOX
from app.profiles.common.xyzplus import (
    execute as xyzplus_execute,
    ZOOM_MAX as xyz_zoom_max,
    ZOOM_MIN as xyz_zoom_min,
    OUTPUT_FORMAT as xyz_output_format,
)
from app.profiles.common.sources import (
    bc_resource_roads,
    trails,
    shelters,
    bc_ates_zones,
    bc_ates_avpaths,
    bc_ates_dec_points,
    bc_ates_poi,
)


NAME = "xyzwinter"
ZOOM_MAX: Final = xyz_zoom_max
ZOOM_MIN: Final = xyz_zoom_min
OUTPUT_FORMAT: Final = xyz_output_format


def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    xyzplus_execute(
        bbox,
        run_id,
        args["xyz_url"],
        NAME,
        bc_ates_zones(bbox, run_id)
        + bc_ates_avpaths(bbox, run_id)
        + bc_ates_poi(bbox, run_id)
        + bc_ates_dec_points(bbox, run_id)
        + bc_resource_roads(bbox, run_id)
        + trails(bbox, run_id)
        + shelters(bbox, run_id),
    )
