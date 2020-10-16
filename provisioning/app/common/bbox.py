import math
from gdal import ogr
from typing import Dict, Final
from pydantic import BaseModel, validator
from pyproj import Transformer, CRS

from app.common.validation import less_than_or_equal_to_other

class BBOX(BaseModel):

    DEFAULT_CRS_CODE = "EPSG:4326"

    max_x: float
    max_y: float
    min_x: float
    min_y: float
    crs_code: str = DEFAULT_CRS_CODE

    def transform_to(self, target_crs_code: str):
        bbox_crs = CRS(self.crs_code)
        target_crs = CRS(target_crs_code)
        transformer = Transformer.from_crs(bbox_crs, target_crs, always_xy = True)
        new_min_x, new_min_y = transformer.transform(self.min_x, self.min_y)
        new_max_x, new_max_y = transformer.transform(self.max_x, self.max_y)
        return BBOX(min_x=new_min_x, min_y=new_min_y, max_x=new_max_x, max_y=new_max_y, crs_code=target_crs_code)

    def as_tuple(self):
        return (self.min_x, self.min_y, self.max_x, self.max_y)

    def get_wkt(self):
        return f"POLYGON (({self.min_x} {self.min_y},{self.max_x} {self.min_y},{self.max_x} {self.max_y},{self.min_x} {self.max_y},{self.min_x} {self.min_y}))"

    def get_centre(self):
        crs = ogr.osr.SpatialReference()
        crs.ImportFromEPSG(int(self.crs_code.split(":")[-1]))
        return ogr.CreateGeometryFromWkt(
            f"POLYGON (({self.min_x} {self.min_y}, {self.max_x} {self.min_y}, {self.max_x} {self.max_y}, {self.min_x} {self.max_y}, {self.min_x} {self.min_y}))",
            reference=crs
        ).Centroid().GetPoint()
