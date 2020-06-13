import re
import os
import logging
import zipfile

from gdal import ogr, DEMProcessing
from typing import Final

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.file import skip_file_creation
from provisioning.app.common.httpRetriever import httpRetriever, RetrievalRequest
from provisioning.app.util import get_data_path, get_output_path

CACHE_DIR_NAME: Final = "bc-hillshade"

def provision(bbox: BBOX) -> None:
    driver = ogr.GetDriverByName("GPKG")
    grid_datasource = (driver.Open(get_data_path("grids.gpkg")))
    grid_layer = grid_datasource.GetLayerByName("Canada-50000")
    grid_layer.SetSpatialFilterRect(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
    bbox_cells = dict()
    while grid_cell := grid_layer.GetNextFeature():
        cell_name = grid_cell.GetFieldAsString("NTS_SNRC")
        cell_parent = re.sub("^0", "", re.search("^\d{2,3}[a-z]", cell_name, re.IGNORECASE)[0])
        for cardinal in ("e", "w"):
            cell_part_name = f"{cell_name.lower()}_{cardinal}"
            zip_file_name = f"{cell_part_name}.dem.zip"
            bbox_cells[cell_part_name] = RetrievalRequest(
                url=f"https://pub.data.gov.bc.ca/datasets/175624/{cell_parent.lower()}/{zip_file_name}",
                path=get_output_path(CACHE_DIR_NAME, zip_file_name),
                expected_type="application/zip"
            )

    httpRetriever(bbox_cells.values())

    for cell_part_name, cell_data in bbox_cells.items():
        dem_name = get_output_path(CACHE_DIR_NAME, f"{cell_part_name}.dem")
        if not skip_file_creation(dem_name):
            with zipfile.ZipFile(cell_data["path"], "r") as zip_ref:
                zip_ref.extractall(get_output_path(CACHE_DIR_NAME))
        hillshade_name = get_output_path(CACHE_DIR_NAME, f"{cell_part_name}_hs.tif")
        if not skip_file_creation(hillshade_name):
            DEMProcessing(hillshade_name, dem_name, "hillshade", format="GTiff", band=1, azimuth=225, altitude=45, scale=1, zFactor=1)

