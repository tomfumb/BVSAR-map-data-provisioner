import glob
import os

from gdal import ogr
from typing import Final, List

from app.common.bbox import BBOX
from app.sources.common.ogr_to_shp import ogr_to_shp
from app.common.util import get_data_path, get_run_data_path


CACHE_DIR_NAME: Final = "bc-ates"
OUTPUT_CRS_CODE: Final = "EPSG:3857"


def provision(
    bbox: BBOX, run_id: str, src_layer_name: str, dst_layer_name: str,
) -> List[str]:
    kmz_driver = ogr.GetDriverByName("LIBKML")
    kmz_datasets = [
        kmz_driver.Open(filename)
        for filename in glob.iglob(
            get_data_path(("avcan-ates-areas-2020-06-23", "**", "*.kmz")),
            recursive=True,
        )
    ]
    run_directory = get_run_data_path(run_id, (CACHE_DIR_NAME,))
    os.makedirs(run_directory, exist_ok=True)
    path = os.path.join(run_directory, f"{dst_layer_name}.shp")
    ogr_to_shp(
        bbox,
        [ds.GetLayerByName(src_layer_name) for ds in kmz_datasets],
        path,
        dst_layer_name,
        OUTPUT_CRS_CODE,
    )
    kmz_datasets = None
    return [path]
