import os

from gdal import ogr
from typing import Final, List

from app.common.bbox import BBOX
from app.sources.common.ogr_to_shp import ogr_to_shp
from app.tilemill.ProjectLayerType import ProjectLayerType
from app.common.util import get_run_data_path
from app.settings import LOCAL_FEATURES_PATH

CACHE_DIR_NAME: Final = "shelters"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.POINT


def provision(bbox: BBOX, run_id: str) -> List[str]:
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("GPKG")
    datasource = driver.Open(LOCAL_FEATURES_PATH)
    path = os.path.join(run_directory, "shelters.shp")
    ogr_to_shp(
        bbox,
        [datasource.GetLayerByName("shelters")],
        path,
        "shelters",
        OUTPUT_CRS_CODE,
    )
    datasource = None
    return [path]
