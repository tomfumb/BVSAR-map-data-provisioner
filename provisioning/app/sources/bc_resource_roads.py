import os

from gdal import ogr
from typing import Final, List

from app.common.bbox import BBOX
from app.sources.common.ogr_to_shp import ogr_to_shp
from app.tilemill.ProjectLayerType import ProjectLayerType
from app.common.util import get_data_path, get_run_data_path

CACHE_DIR_NAME: Final = "bc-resource-roads"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.LINESTRING


def provision(bbox: BBOX, run_id: str) -> List[str]:
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    datasource = driver.Open(
        get_data_path(
            (
                "WHSE_FOREST_TENURE_FTEN_ROAD_SECTION_LINES_SVW",
                "WHSE_FOREST_TENURE_FTEN_ROAD_SECTION_LINES_SVW.shp",
            )
        )
    )
    path = os.path.join(run_directory, "bc_resource_roads.shp")
    ogr_to_shp(
        bbox,
        [datasource.GetLayerByIndex(0)],
        path,
        "bc_resource_roads",
        OUTPUT_CRS_CODE,
    )
    datasource = None
    return [path]
