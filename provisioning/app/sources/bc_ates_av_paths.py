import glob
import os

from gdal import ogr
from typing import Final, List

from app.common.BBOX import BBOX
from app.tilemill.ProjectLayerType import ProjectLayerType
from app.sources.common.ogr_to_shp import ogr_to_shp
from app.sources.common.bc_ates import provision as bc_ates_provisioner, OUTPUT_CRS_CODE, CACHE_DIR_NAME
from app.common.util import get_data_path, get_run_data_path


OUTPUT_TYPE: Final = ProjectLayerType.LINESTRING

def provision(bbox: BBOX, run_id: str) -> List[str]:
    return bc_ates_provisioner(bbox, run_id, "Avalanche paths", "bc_ates_av_paths")
