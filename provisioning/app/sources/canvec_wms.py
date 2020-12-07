from typing import Dict, Final, List, Tuple

from app.common.bbox import BBOX
from app.sources.common.wms import (
    provision as wms_provisioner,
    OUTPUT_TYPE as WMS_OUTPUT_TYPE,
    WmsProperties,
)

CACHE_DIR_NAME: Final = "canvec"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = WMS_OUTPUT_TYPE
HTTP_RETRIEVAL_CONCURRENCY: Final = 2


def provision(bbox: BBOX, scales: Tuple[int], run_id: str) -> Dict[int, List[str]]:
    return wms_provisioner(
        bbox,
        "http://maps.geogratis.gc.ca/wms/canvec_en",
        WmsProperties(max_width=4096, max_height=4096),
        OUTPUT_CRS_CODE,
        ("canvec",),
        tuple(),
        scales,
        "png",
        CACHE_DIR_NAME,
        run_id,
        HTTP_RETRIEVAL_CONCURRENCY,
    )
