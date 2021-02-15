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


CACHE_DIR_NAME: Final = "bc-parcels"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.POLYGON


def provision(bbox: BBOX, run_id: str) -> List[str]:
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("GPKG")
    datasource = driver.Open(get_data_path(("pmbc_parcel_fabric_poly_svw.gpkg",)))
    parcels_layer = datasource.GetLayerByName("pmbc_parcel_fabric_poly_svw")
    parcels_layer.SetAttributeFilter(
        "OWNER_TYPE IN ('First Nation','Mixed Ownership','Municipal','Private','Unknown')"
    )
    path = os.path.join(run_directory, "bc_parcels.shp")
    ogr_to_shp(
        bbox, [parcels_layer], path, "bc_parcels", OUTPUT_CRS_CODE,
    )
    parcels_layer = None
    datasource = None
    return [path]
