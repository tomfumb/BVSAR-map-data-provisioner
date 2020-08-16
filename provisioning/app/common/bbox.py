from gdal import ogr
from typing import Dict, Final
from pydantic import BaseModel, validator

from app.common.validation import less_than_or_equal_to_other

class BBOX(BaseModel):

    CRS_CODE = "EPSG:4326"

    max_x: float
    max_y: float
    min_x: float
    min_y: float

    def as_tuple(self):
        return (self.min_x, self.min_y, self.max_x, self.max_y)

    def get_wkt(self):
        return f"POLYGON (({self.min_x} {self.min_y},{self.max_x} {self.min_y},{self.max_x} {self.max_y},{self.min_x} {self.max_y},{self.min_x} {self.min_y}))"

    def get_centre(self):
        return ogr.CreateGeometryFromWkt(
            f"POLYGON (({self.min_x} {self.min_y}, {self.max_x} {self.min_y}, {self.max_x} {self.max_y}, {self.min_x} {self.max_y}, {self.min_x} {self.min_y}))"
        ).Centroid().GetPoint()

    def within_range(cls, value: object, min: float, max: float):
        return (isinstance(value, int) or isinstance(value, float)) and value >= min and value <= max

    @validator("min_x")
    def min_x_validator(cls, value, values):
        if cls.within_range(cls, value, -180, 180) and less_than_or_equal_to_other(value, "max_x", values):
            return value
        else:
            raise ValueError("Min X must be betwen -180 and 180 and less than Max X")

    @validator("min_y")
    def min_y_validator(cls, value, values):
        if cls.within_range(cls, value, -90, 90) and less_than_or_equal_to_other(value, "max_y", values):
            return value
        else:
            raise ValueError("Min Y must be betwen -90 and 90 and less than Max Y")

    @validator("max_x")
    def max_x_validator(cls, value):
        if cls.within_range(cls, value, -180, 180):
            return value
        else:
            raise ValueError("Max X must be betwen -180 and 180 and greater than Min X")

    @validator("max_y")
    def max_y_validator(cls, value):
        if cls.within_range(cls, value, -90, 90):
            return value
        else:
            raise ValueError("Max Y must be betwen -90 and 90 and greater than Min Y")
