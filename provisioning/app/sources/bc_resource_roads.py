import os

from gdal import ogr
from typing import Final, List

from provisioning.app.common.bbox import BBOX
from provisioning.app.sources.common.ogr_to_shp import ogr_to_shp
from provisioning.app.tilemill.ProjectLayerType import ProjectLayerType
from provisioning.app.util import delete_directory_contents, get_data_path, get_cache_path

CACHE_DIR_NAME: Final = "bc-resource-roads"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.LINESTRING

def provision(bbox: BBOX) -> List[str]:
    output_dir = get_cache_path((CACHE_DIR_NAME,))
    os.makedirs(output_dir, exist_ok = True)
    delete_directory_contents(output_dir)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    datasource = driver.Open(get_data_path(("FTEN_ROAD_SECTION_LINES_SVW","FTEN_RS_LN_line.shp")))
    result = ogr_to_shp(
        bbox,
        datasource.GetLayerByIndex(0),
        get_cache_path((CACHE_DIR_NAME, "bc_resource_roads.shp")),
        "bc_resource_roads",
        OUTPUT_CRS_CODE
    )
    datasource = None
    return result