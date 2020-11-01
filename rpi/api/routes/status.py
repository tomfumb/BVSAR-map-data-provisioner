import random
import math


from shutil import disk_usage

from fastapi.routing import APIRouter

from api.settings import UPLOADS_DIR

router = APIRouter()


@router.get("")
async def get_status():
    return {
        "space": {"available": disk_usage(UPLOADS_DIR)[2],},
        "power": {"remaining": _remaining_power_estimate(),},
    }


def _remaining_power_estimate() -> float:
    return math.ceil(random.random() * 10000) / 100
