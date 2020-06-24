import os

from gdal import ogr
from typing import Final, List

from provisioning.app.common.bbox import BBOX
from provisioning.app.sources.common.ogr_to_shp import ogr_to_shp
from provisioning.app.tilemill.ProjectLayerType import ProjectLayerType
from provisioning.app.util import get_data_path, get_run_data_path

CACHE_DIR_NAME: Final = "shelters"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.POINT

def provision(bbox: BBOX, run_id: str) -> List[str]:
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("GPKG")
    datasource = driver.Open(get_data_path(("relevant-features.gpkg",)))
    result = ogr_to_shp(
        bbox,
        datasource.GetLayerByName("shelters"),
        os.path.join(run_directory, "shelters.shp"),
        "shelters",
        OUTPUT_CRS_CODE
    )
    datasource = None
    return result
