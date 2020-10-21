import logging
import os

from gdal import ogr
from typing import Final, List

from app.common.BBOX import BBOX
from app.common.ftp_retriever import retrieve_directory
from app.common.util import get_run_data_path
from app.sources.common.ogr_to_shp import ogr_to_shp
from app.tilemill.ProjectLayerType import ProjectLayerType


CACHE_DIR_NAME: Final = "bc-wetlands"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.POLYGON


def provision(bbox: BBOX, run_id: str) -> List[str]:
    logging.info(
        "Retrieving BC Freshwater Atlas - this could take a while the first time"
    )
    fgdb = retrieve_directory(
        "ftp.geobc.gov.bc.ca", "/sections/outgoing/bmgs/FWA_Public/FWA_BC.gdb"
    )
    logging.info("Retrieved BC Freshwater Atlas")
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("OpenFileGDB")
    datasource = driver.Open(fgdb)
    result = ogr_to_shp(
        bbox,
        [datasource.GetLayerByName("FWA_WETLANDS_POLY")],
        os.path.join(run_directory, "bc_wetlands.shp"),
        "bc_wetlands",
        OUTPUT_CRS_CODE,
    )
    datasource = None
    return result
