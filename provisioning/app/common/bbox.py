import json

from osgeo import ogr, osr
from pydantic import BaseModel


class BBOX(BaseModel):

    DEFAULT_CRS_CODE = "EPSG:4326"

    max_x: float
    max_y: float
    min_x: float
    min_y: float
    crs_code: str = DEFAULT_CRS_CODE

    def as_tuple(self):
        return (self.min_x, self.min_y, self.max_x, self.max_y)

    def as_gdal_win(self):
        return (self.min_x, self.max_y, self.max_x, self.min_y)

    def as_gdal_win(self, target_crs_code: str):
        transformed_geom = self.transform_as_geom(target_crs_code)
        envelope = transformed_geom.GetEnvelope()
        return (envelope[0], envelope[3], envelope[1], envelope[2])

    def get_wkt(self):
        return f"POLYGON (({self.min_x} {self.min_y},{self.max_x} {self.min_y},{self.max_x} {self.max_y},{self.min_x} {self.max_y},{self.min_x} {self.min_y}))"

    def get_centre(self):
        crs = ogr.osr.SpatialReference()
        crs.ImportFromEPSG(int(self.crs_code.split(":")[-1]))
        return ogr.CreateGeometryFromWkt(self.get_wkt()).Centroid().GetPoint()

    def transform_as_geom(self, target_crs_code: str) -> ogr.Geometry:
        if self.crs_code == target_crs_code:
            return ogr.CreateGeometryFromWkt(self.get_wkt())
        srs_in = osr.SpatialReference()
        srs_in.SetFromUserInput(self.crs_code)
        srs_out = osr.SpatialReference()
        srs_out.SetFromUserInput(target_crs_code)
        bbox_geom = ogr.CreateGeometryFromWkt(self.get_wkt(), srs_in)
        bbox_coords = json.loads(bbox_geom.ExportToJson())
        bbox_coords_transformed = list()
        for bbox_point_pair in bbox_coords["coordinates"][0]:
            point = ogr.Geometry(ogr.wkbPoint)
            point.AssignSpatialReference(srs_in)
            point.AddPoint(bbox_point_pair[0], bbox_point_pair[1])
            point.TransformTo(srs_out)
            x, y, _ = point.GetPoint()
            bbox_coords_transformed.append([x, y])
        bbox_coords["coordinates"][0] = bbox_coords_transformed
        bbox_transformed_geom = ogr.CreateGeometryFromJson(json.dumps(bbox_coords))
        bbox_transformed_geom.AssignSpatialReference(srs_out)
        return bbox_transformed_geom
