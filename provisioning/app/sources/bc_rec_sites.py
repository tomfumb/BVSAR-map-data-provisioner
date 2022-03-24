import os

from osgeo import ogr
from typing import Final, List

from app.common.bbox import BBOX
from app.common.util import (
    get_run_data_path,
    get_data_path,
)
from app.sources.common.ogr_to_shp import ogr_to_shp
from app.tilemill.ProjectLayerType import ProjectLayerType


CACHE_DIR_NAME: Final = "bc-rec-sites"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.POLYGON


def provision(bbox: BBOX, run_id: str) -> List[str]:
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("OpenFileGDB")
    datasource = driver.Open(get_data_path(("FTEN_RECREATION_POLY_SVW.gdb",)))
    rec_sites_layer = datasource.GetLayerByName(
        "WHSE_FOREST_TENURE_FTEN_RECREATION_POLY_SVW"
    )
    rec_sites_layer.SetAttributeFilter("LIFE_CYCLE_STATUS_CODE IN ('ACTIVE','PENDING')")
    path = os.path.join(run_directory, "bc_rec_sites.shp")
    ogr_to_shp(
        bbox, [rec_sites_layer], path, "bc_rec_sites", OUTPUT_CRS_CODE,
    )
    rec_sites_layer = None
    datasource = None
    return [path]
