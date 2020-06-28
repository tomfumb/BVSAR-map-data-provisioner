from typing import Dict, Final, List, Tuple

from app.common.bbox import BBOX
from app.util import get_cache_path, get_run_data_path
from app.sources.common.wms import provision as wms_provisioner, OUTPUT_TYPE as WMS_OUTPUT_TYPE, WmsProperties
from app.tilemill.ProjectLayerType import ProjectLayerType

CACHE_DIR_NAME: Final = "canvec"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = WMS_OUTPUT_TYPE

def provision(bbox: BBOX, scales: Tuple[int], run_id: str) -> Dict[int, List[str]]:
    return wms_provisioner(bbox, "http://maps.geogratis.gc.ca/wms/canvec_en", WmsProperties(max_width=4096, max_height=4096), OUTPUT_CRS_CODE, ("canvec",), tuple(), scales, "png", CACHE_DIR_NAME, run_id)
