import re
import os
import logging
import zipfile

from gdal import ogr, Warp
from typing import Dict, Final, List

from app.common.bbox import BBOX
from app.common.file import skip_file_creation, remove_intermediaries
from app.common.get_datasource_from_bbox import get_datasource_from_bbox, BBOX_LAYER_NAME
from app.common.httpRetriever import httpRetriever, RetrievalRequest
from app.tilemill.ProjectLayerType import ProjectLayerType
from app.util import get_data_path, get_cache_path, get_run_data_path

CACHE_DIR_NAME: Final = "bc-topo-20000"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.RASTER

class GenerationRequest(RetrievalRequest):
    cell_name: str
    tif_name: str
    tif_path: str
    prj_path: str
    run_path: str

def provision(bbox: BBOX, run_id: str) -> List[str]:
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory)
    driver = ogr.GetDriverByName("GPKG")
    grid_datasource = (driver.Open(get_data_path(("grids.gpkg",))))
    grid_layer = grid_datasource.GetLayerByName("BC-20000")
    grid_layer.SetSpatialFilterRect(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
    bbox_cells = list()
    while grid_cell := grid_layer.GetNextFeature():
        cell_name = grid_cell.GetFieldAsString("MAP_TILE")
        cell_parent = re.search("^\d{2,3}[a-z]", cell_name, re.IGNORECASE)[0]
        bbox_cells.append(GenerationRequest(
            url=f"https://pub.data.gov.bc.ca/datasets/177864/tif/bcalb/{cell_parent}/{cell_name}.zip",
            path=get_cache_path((CACHE_DIR_NAME, f"{cell_name}.zip")),
            expected_type="application/zip",
            cell_name=cell_name,
            tif_name=f"{cell_name}.tif",
            tif_path=get_cache_path((CACHE_DIR_NAME, f"{cell_name}.tif")),
            prj_path=get_cache_path((CACHE_DIR_NAME, f"{cell_name}_prj.tif")),
            run_path=get_run_data_path(run_id, (CACHE_DIR_NAME, f"{cell_name}.tif"))
        ))

    to_generate = list(filter(lambda generation_request: not skip_file_creation(generation_request.prj_path), bbox_cells))
    httpRetriever(to_generate)

    for generation_request in to_generate:
        try:
            with zipfile.ZipFile(generation_request.path, "r") as zip_ref:
                zip_ref.extract(generation_request.tif_name, get_cache_path((CACHE_DIR_NAME,)))
            Warp(
                generation_request.prj_path,
                generation_request.tif_path,
                cutlineDSName=get_data_path(("grids.gpkg",)),
                cutlineLayer="BC-20000",
                cutlineWhere=f"MAP_TILE = '{generation_request.cell_name}'",
                cropToCutline=True,
                dstNodata=-1,
                srcSRS="EPSG:26909",
                dstSRS=OUTPUT_CRS_CODE,
                resampleAlg="lanczos"
            )
            if remove_intermediaries():
                os.remove(generation_request.path)
                os.remove(generation_request.tif_path)
        except Exception as ex:
            logging.error(ex)

    for generation_request in bbox_cells:
        Warp(generation_request.run_path, generation_request.prj_path, cutlineDSName=get_datasource_from_bbox(bbox, get_run_data_path(run_id, None)), cutlineLayer=BBOX_LAYER_NAME, cropToCutline=True, dstNodata=-1)

    return list(map(lambda generation_request: generation_request.run_path, bbox_cells))

def _get_final_path(cell_name: str) -> str:
    return get_cache_path((CACHE_DIR_NAME, f"{cell_name}_prj.tif"))
