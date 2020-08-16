from typing import Tuple, Callable
from pydantic import BaseModel, validator

from app.common.validation import less_than_or_equal_to_other


class Profile(BaseModel):
    provisioners: Tuple[Callable, ...]
    stylesheets: Tuple[str, ...]
    zoom_max: int
    zoom_min: int
    zoom_xyz_max: int = None
    zoom_xyz_min: int = None

    def has_xyz(self):
        return self.zoom_xyz_min is not None and self.zoom_xyz_max is not None

    @validator("zoom_min")
    def zoom_min_validator(cls, value, values):
        if less_than_or_equal_to_other(value, "zoom_max", values):
            return value
        else:
            raise ValueError("zoom min must be <= zoom max")

    @validator("zoom_xyz_min")
    def zoom_xyz_min_validator(cls, value, values):
        if less_than_or_equal_to_other(value, "zoom_xyz_max", values):
            return value
        else:
            raise ValueError("zoom xyz min must be <= zoom xyz max")
