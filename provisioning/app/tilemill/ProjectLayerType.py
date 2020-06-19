from enum import Enum

class ProjectLayerType(str, Enum):
    RASTER = "raster"
    LINESTRING = "linestring"
    POINT = "point"