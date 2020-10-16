from typing import List, Tuple

from app.common.BBOX import BBOX
from app.profiles.Profile import Profile


def get_profile(bbox: BBOX, run_id: str) -> Profile:

    return Profile(
        provisioners=(),
        stylesheets=(),
        zoom_min=0,
        zoom_max=17,
        zoom_xyz_min=0,
        zoom_xyz_max=17,
    )
