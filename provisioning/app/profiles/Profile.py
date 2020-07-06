from typing import Tuple, Callable
from pydantic import BaseModel


class Profile(BaseModel):
    provisioners: Tuple[Callable, ...]
    stylesheets: Tuple[str, ...]
    zoom_min: int
    zoom_max: int
    zoom_xyz_min: int = None
    zoom_xyz_max: int = None

    def has_xyz(self):
        return self.zoom_xyz_min is not None and self.zoom_xyz_max is not None
