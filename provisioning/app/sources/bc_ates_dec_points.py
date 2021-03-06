from typing import Final, List

from app.common.bbox import BBOX
from app.tilemill.ProjectLayerType import ProjectLayerType
from app.sources.common.bc_ates import (
    provision as bc_ates_provisioner,
    OUTPUT_CRS_CODE as bc_ates_output_crs_code,
    CACHE_DIR_NAME as bc_ates_cache_dir_name,
)

OUTPUT_CRS_CODE: Final = bc_ates_output_crs_code
CACHE_DIR_NAME: Final = bc_ates_cache_dir_name
OUTPUT_TYPE: Final = ProjectLayerType.POINT


def provision(bbox: BBOX, run_id: str) -> List[str]:
    return bc_ates_provisioner(bbox, run_id, "Decision points", "bc_ates_dec_points")
