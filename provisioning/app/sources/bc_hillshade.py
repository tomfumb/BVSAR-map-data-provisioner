import re
import os
import logging
import zipfile

from gdal import ogr, DEMProcessing, Warp
from typing import Final, List

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.file import skip_file_creation, remove_intermediaries
from provisioning.app.common.httpRetriever import httpRetriever, RetrievalRequest
from provisioning.app.tilemill.ProjectLayerType import ProjectLayerType
from provisioning.app.util import get_data_path, get_output_path

CACHE_DIR_NAME: Final = "bc-hillshade"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.RASTER

def provision(bbox: BBOX) -> List[str]:
    driver = ogr.GetDriverByName("GPKG")
    grid_datasource = (driver.Open(get_data_path(("grids.gpkg",))))
    grid_layer = grid_datasource.GetLayerByName("Canada-50000")
    grid_layer.SetSpatialFilterRect(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
    bbox_cells = dict()
    grid_files = list()
    while grid_cell := grid_layer.GetNextFeature():
        cell_name = grid_cell.GetFieldAsString("NTS_SNRC")
        cell_parent = re.sub("^0", "", re.search("^\d{2,3}[a-z]", cell_name, re.IGNORECASE)[0])
        for cardinal in ("e", "w"):
            cell_part_name = f"{cell_name.lower()}_{cardinal}"
            final_path = _get_final_path(cell_part_name)
            grid_files.append(final_path)
            if not skip_file_creation(final_path):
                zip_file_name = f"{cell_part_name}.dem.zip"
                bbox_cells[cell_part_name] = RetrievalRequest(
                    url=f"https://pub.data.gov.bc.ca/datasets/175624/{cell_parent.lower()}/{zip_file_name}",
                    path=get_output_path(CACHE_DIR_NAME, zip_file_name),
                    expected_type="application/zip"
                )

    httpRetriever(list(bbox_cells.values()))

    for cell_part_name, retrieval_request in bbox_cells.items():
        dem_name = get_output_path(CACHE_DIR_NAME, f"{cell_part_name}.dem")
        with zipfile.ZipFile(retrieval_request.path, "r") as zip_ref:
            zip_ref.extractall(get_output_path(CACHE_DIR_NAME))
        prj_name = get_output_path(CACHE_DIR_NAME, f"{cell_part_name}_prj.tif")
        Warp(prj_name, dem_name, srcSRS="EPSG:4269", dstSRS=OUTPUT_CRS_CODE, resampleAlg="cubic")
        DEMProcessing(_get_final_path(cell_part_name), prj_name, "hillshade", format="GTiff", band=1, azimuth=225, altitude=45, scale=1, zFactor=1)
        if remove_intermediaries():
            os.remove(retrieval_request.path)
            os.remove(prj_name)
            os.remove(dem_name)

    return grid_files

def _get_final_path(cell_name: str) -> str:
    return get_output_path(CACHE_DIR_NAME, f"{cell_name}_hs.tif")