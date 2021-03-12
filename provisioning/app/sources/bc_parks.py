import os

from gdal import ogr
from typing import Final, List

from app.common.bbox import BBOX
from app.common.util import (
    get_run_data_path,
    get_data_path,
)
from app.sources.common.ogr_to_shp import ogr_to_shp
from app.tilemill.ProjectLayerType import ProjectLayerType


CACHE_DIR_NAME: Final = "bc-parks"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.POLYGON


def provision(bbox: BBOX, run_id: str) -> List[str]:
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("OpenFileGDB")
    datasource = driver.Open(get_data_path(("TA_PARK_ECORES_PA_SVW.gdb",)))
    parks_layer = datasource.GetLayerByName("WHSE_TANTALIS_TA_PARK_ECORES_PA_SVW")
    path = os.path.join(run_directory, "bc_parks.shp")
    ogr_to_shp(
        bbox, [parks_layer], path, "bc_parks", OUTPUT_CRS_CODE,
    )
    parks_layer = None
    datasource = None
    return [path]
