from typing import Dict, Final

from app.common.bbox import BBOX
from app.profiles.common.xyzplus import (
    execute as xyzplus_execute,
    ZOOM_MAX,
    ZOOM_MIN,
    OUTPUT_FORMAT as xyz_output_format,
)
from app.profiles.common.sources import (
    bc_resource_roads,
    trails,
    shelters,
    bc_wetlands,
    bc_waterways,
)


NAME: Final = "xyzsummer"
OUTPUT_FORMAT: Final = xyz_output_format


def execute(bbox: BBOX, run_id: str, args: Dict[str, object] = dict()) -> None:
    xyzplus_execute(
        bbox,
        run_id,
        args["xyz_url"],
        NAME,
        ZOOM_MAX,
        ZOOM_MIN,
        bc_waterways(bbox, run_id)
        + bc_wetlands(bbox, run_id)
        + bc_resource_roads(bbox, run_id)
        + trails(bbox, run_id)
        + shelters(bbox, run_id),
        ["common-summer"],
    )
