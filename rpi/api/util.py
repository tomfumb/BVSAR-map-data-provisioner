from hashlib import md5
from json import dumps


def get_name_for_bounds(
    prefix: str, x_min: float, y_min: float, x_max: float, y_max: float
) -> str:
    return f"{prefix}-{md5(dumps([x_min, y_min, x_max, y_max]).encode('UTF-8')).hexdigest()}"
