import logging
import os

from osgeo import ogr
from typing import Final, List

from app.common.bbox import BBOX
from app.common.ftp_retriever import fetch
from app.common.util import get_run_data_path
from app.sources.common.ogr_to_shp import ogr_to_provided
from app.tilemill.ProjectLayerType import ProjectLayerType
import zipfile

from app.common.util import get_cache_path


CACHE_DIR_NAME: Final = "bc-waterways"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.LINESTRING


def provision(bbox: BBOX, run_id: str) -> List[str]:
    logging.info(
        "Retrieving BC Freshwater Atlas - this could take a while the first time"
    )
    zip_path = fetch(
        "FWA_BC.zip", "ftp.geobc.gov.bc.ca", "/sections/outgoing/bmgs/FWA_Public"
    )
    fgdb_dir = os.path.dirname(zip_path)
    fgdb = os.path.join(fgdb_dir, "FWA_BC.gdb")
    if not os.path.exists(fgdb):
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(get_cache_path((fgdb_dir,)))
    logging.info("Retrieved BC Freshwater Atlas")
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    src_driver = ogr.GetDriverByName("OpenFileGDB")
    src_datasource = src_driver.Open(fgdb)
    mem_driver = ogr.GetDriverByName("Memory")
    mem_datasource = mem_driver.CreateDataSource("")
    logging.info("Clipping waterways for bbox")
    ogr_to_provided(
        bbox,
        [src_datasource.GetLayerByName("FWA_ROUTES_SP")],
        mem_datasource,
        "waterways",
        OUTPUT_CRS_CODE,
    )
    logging.info("Clipping lakes for bbox")
    ogr_to_provided(
        bbox,
        [src_datasource.GetLayerByName("FWA_LAKES_POLY")],
        mem_datasource,
        "lakes",
        OUTPUT_CRS_CODE,
    )
    logging.info("Clipping rivers for bbox")
    ogr_to_provided(
        bbox,
        [src_datasource.GetLayerByName("FWA_RIVERS_POLY")],
        mem_datasource,
        "rivers",
        OUTPUT_CRS_CODE,
    )
    logging.info("Clipping wetlands for bbox")
    ogr_to_provided(
        bbox,
        [src_datasource.GetLayerByName("FWA_WETLANDS_POLY")],
        mem_datasource,
        "wetlands",
        OUTPUT_CRS_CODE,
    )
    waterways_layer = mem_datasource.GetLayerByName("waterways")
    lakes_layer = mem_datasource.GetLayerByName("lakes")
    rivers_layer = mem_datasource.GetLayerByName("rivers")
    wetlands_layer = mem_datasource.GetLayerByName("wetlands")
    dst_srs = ogr.osr.SpatialReference()
    dst_srs.ImportFromEPSG(int(OUTPUT_CRS_CODE.split(":")[-1]))
    no_lakes_layer = mem_datasource.CreateLayer(
        "no_lakes", dst_srs, waterways_layer.GetLayerDefn().GetGeomType()
    )
    no_rivers_layer = mem_datasource.CreateLayer(
        "no_rivers", dst_srs, waterways_layer.GetLayerDefn().GetGeomType()
    )
    no_wetlands_layer = mem_datasource.CreateLayer(
        "no_wetlands", dst_srs, waterways_layer.GetLayerDefn().GetGeomType()
    )
    logging.info("Erasing intersections - lakes")
    waterways_layer.Erase(lakes_layer, no_lakes_layer)
    logging.info("Erasing intersections - rivers")
    no_lakes_layer.Erase(rivers_layer, no_rivers_layer)
    logging.info("Erasing intersections - wetlands")
    no_rivers_layer.Erase(wetlands_layer, no_wetlands_layer)

    logging.info("Writing waterways")
    dst_path = os.path.join(run_directory, "bc_waterways.shp")
    dst_driver = ogr.GetDriverByName("ESRI Shapefile")
    dst_datasource = dst_driver.CreateDataSource(dst_path)
    dst_datasource.CopyLayer(no_wetlands_layer, "bc_waterways")
    src_datasource = None
    mem_datasource = None
    dst_datasource = None
    return [dst_path]
