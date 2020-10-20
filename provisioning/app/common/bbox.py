import math
from gdal import ogr, osr
from typing import Dict, Final, Tuple
from pydantic import BaseModel, validator
from pyproj import Proj, transform, Transformer, CRS

from app.common.validation import less_than_or_equal_to_other

class BBOX(BaseModel):

    DEFAULT_CRS_CODE = "EPSG:4326"

    max_x: float
    max_y: float
    min_x: float
    min_y: float
    crs_code: str = DEFAULT_CRS_CODE


    def as_tuple(self):
        return (self.min_x, self.min_y, self.max_x, self.max_y)

    def get_wkt(self):
        return f"POLYGON (({self.min_x} {self.min_y},{self.max_x} {self.min_y},{self.max_x} {self.max_y},{self.min_x} {self.max_y},{self.min_x} {self.min_y}))"

    def get_centre(self):
        crs = ogr.osr.SpatialReference()
        crs.ImportFromEPSG(int(self.crs_code.split(":")[-1]))
        return ogr.CreateGeometryFromWkt(self.get_wkt()).Centroid().GetPoint()
