from typing import Tuple, Callable
from pydantic import BaseModel


class Profile(BaseModel):
    provisioners: Tuple[Callable, ...]
    stylesheets: Tuple[str, ...]
    zooms: Tuple[int, ...]
    zooms_xyz: Tuple[int, ...]
