import re
import os
import logging
import zipfile

from gdal import ogr, Warp
from typing import Dict, Final

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.file import skip_file_creation, remove_intermediaries
from provisioning.app.common.httpRetriever import httpRetriever, RetrievalRequest
from provisioning.app.util import get_data_path, get_output_path

CACHE_DIR_NAME: Final = "bc-topo-20000"
OUTPUT_CRS_CODE: Final = "EPSG:3857"

def provision(bbox: BBOX):
    driver = ogr.GetDriverByName("GPKG")
    grid_datasource = (driver.Open(get_data_path("grids.gpkg")))
    grid_layer = grid_datasource.GetLayerByName("BC-20000")
    grid_layer.SetSpatialFilterRect(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
    retrieval_requests = dict()
    grid_files = list()
    while grid_cell := grid_layer.GetNextFeature():
        cell_name = grid_cell.GetFieldAsString("MAP_TILE")
        final_path = _get_final_path(cell_name)
        grid_files.append(final_path)
        if not skip_file_creation(final_path):
            cell_parent = re.search("^\d{2,3}[a-z]", cell_name, re.IGNORECASE)[0]
            retrieval_requests[cell_name] = RetrievalRequest(
                url=f"https://pub.data.gov.bc.ca/datasets/177864/tif/bcalb/{cell_parent}/{cell_name}.zip",
                path=get_output_path(CACHE_DIR_NAME, f"{cell_name}.zip"),
                expected_type="application/zip"
            )

    httpRetriever(list(retrieval_requests.values()))

    for cell_name, retrieval_request in retrieval_requests.items():
        unzipped_tif_name = f"{cell_name}.tif"
        unzipped_tif_location = get_output_path(CACHE_DIR_NAME, unzipped_tif_name)
        with zipfile.ZipFile(retrieval_request.path, "r") as zip_ref:
            zip_ref.extract(unzipped_tif_name, get_output_path(CACHE_DIR_NAME))
        Warp(
            _get_final_path(cell_name),
            unzipped_tif_location,
            cutlineDSName=get_data_path("grids.gpkg"),
            cutlineLayer="BC-20000",
            cutlineWhere=f"MAP_TILE = '{cell_name}'",
            cropToCutline=True,
            dstNodata=-1,
            srcSRS="EPSG:26909",
            dstSRS=OUTPUT_CRS_CODE,
            resampleAlg="lanczos"
        )
        if remove_intermediaries():
            os.remove(retrieval_request.path)
            os.remove(unzipped_tif_location)
    
    return grid_files

def _get_final_path(cell_name: str) -> str:
    return get_output_path(CACHE_DIR_NAME, f"{cell_name}_prj.tif")
