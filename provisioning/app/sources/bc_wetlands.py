import logging
import os

from osgeo import ogr
from typing import Final, List
import zipfile
from app.common.bbox import BBOX
from app.common.ftp_retriever import fetch
from app.common.util import get_run_data_path
from app.sources.common.ogr_to_shp import ogr_to_shp
from app.tilemill.ProjectLayerType import ProjectLayerType
from app.common.util import get_cache_path


CACHE_DIR_NAME: Final = "bc-wetlands"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.POLYGON


def provision(bbox: BBOX, run_id: str) -> List[str]:
    logging.info(
        "Retrieving BC Freshwater Atlas - this could take a while the first time"
    )
    zip_path = fetch("FWA_BC.zip", "ftp.geobc.gov.bc.ca", "/sections/outgoing/bmgs/FWA_Public")
    fgdb_dir = os.path.dirname(zip_path)
    fgdb = os.path.join(fgdb_dir, "FWA_BC.gdb")
    if not os.path.exists(fgdb):
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(get_cache_path((fgdb,)))
    logging.info("Retrieved BC Freshwater Atlas")
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("OpenFileGDB")
    datasource = driver.Open(fgdb)
    path = os.path.join(run_directory, "bc_wetlands.shp")
    ogr_to_shp(
        bbox,
        [datasource.GetLayerByName("FWA_WETLANDS_POLY")],
        path,
        "bc_wetlands",
        OUTPUT_CRS_CODE,
    )
    datasource = None
    return [path]
