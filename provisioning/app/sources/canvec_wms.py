from typing import Dict, Final, List, Tuple

from provisioning.app.common.bbox import BBOX
from provisioning.app.util import get_cache_path, get_run_data_path
from provisioning.app.sources.common.wms import provision as wms_provisioner, OUTPUT_TYPE as WMS_OUTPUT_TYPE
from provisioning.app.tilemill.ProjectLayerType import ProjectLayerType

CACHE_DIR_NAME: Final = "canvec"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = WMS_OUTPUT_TYPE

def provision(bbox: BBOX, scales: Tuple[int], run_id: str) -> Dict[int, List[str]]:
    return wms_provisioner(bbox, "https://maps.geogratis.gc.ca/wms/canvec_en", OUTPUT_CRS_CODE, ("canvec",), tuple(), scales, "png", get_cache_path((CACHE_DIR_NAME,)), get_run_data_path(run_id, (CACHE_DIR_NAME,)))
