import re
import os
import logging
import zipfile

from gdal import ogr, Warp
from typing import Final

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.file import skip_file_creation
from provisioning.app.common.httpRetriever import httpRetriever, RetrievalRequest
from provisioning.app.util import get_data_path, get_output_path

CACHE_DIR_NAME: Final = "bc-topo-20000"

def provision(bbox: BBOX):
    driver = ogr.GetDriverByName("GPKG")
    grid_datasource = (driver.Open(get_data_path("grids.gpkg")))
    grid_layer = grid_datasource.GetLayerByName("BC-20000")
    grid_layer.SetSpatialFilterRect(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
    bbox_cells = dict()
    while grid_cell := grid_layer.GetNextFeature():
        cell_name = grid_cell.GetFieldAsString("MAP_TILE")
        cell_parent = re.search("^\d{2,3}[a-z]", cell_name, re.IGNORECASE)[0]
        bbox_cells[cell_name] = RetrievalRequest(
            url=f"https://pub.data.gov.bc.ca/datasets/177864/tif/bcalb/{cell_parent}/{cell_name}.zip",
            path=get_output_path(CACHE_DIR_NAME, f"{cell_name}.zip"),
            expected_type="application/zip"
        )

    httpRetriever(bbox_cells.values())

    tif_crops = list()
    for cell_name, cell_data in bbox_cells.items():
        tif_name = get_output_path(CACHE_DIR_NAME, f"{cell_name}.tif")
        if not skip_file_creation(tif_name):
            with zipfile.ZipFile(cell_data["path"], "r") as zip_ref:
                zip_ref.extract(f"{cell_name}.tif", get_output_path(CACHE_DIR_NAME))
        
        tif_crop_name = get_output_path(CACHE_DIR_NAME, f"{cell_name}_crop.tif")
        if not skip_file_creation(tif_crop_name):
            result = Warp(
                tif_crop_name,
                tif_name,
                cutlineDSName=get_data_path("grids.gpkg"),
                cutlineLayer="BC-20000",
                cutlineWhere=f"MAP_TILE = '{cell_name}'",
                cropToCutline=True,
                dstNodata=-1
            )
            result = None
        # tif_crops.append(tif_crop_name)
    
    # Warp(get_output_path(CACHE_DIR_NAME, "merge.tif"), tif_crops)
    
    # return a list of images that cover the provided BBOX
    return tif_crops
