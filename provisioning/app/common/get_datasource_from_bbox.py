import os

from gdal import ogr, osr
from typing import Final

from app.common.BBOX import BBOX

BBOX_LAYER_NAME: Final = "bbox"
BBOX_GPKG_NAME: Final = "bbox.gpkg"


def get_datasource_from_bbox(bbox: BBOX, output_dir: str) -> None:
    driver = ogr.GetDriverByName("GPKG")
    gpkg_path = os.path.join(output_dir, BBOX_GPKG_NAME)
    datasource = driver.Open(gpkg_path)
    if not datasource:
        datasource = driver.CreateDataSource(gpkg_path)
    layer = datasource.GetLayerByName(BBOX_LAYER_NAME)
    srs = osr.SpatialReference()
    srs.SetFromUserInput(bbox.crs_code)
    if not layer:
        layer = datasource.CreateLayer(BBOX_LAYER_NAME, srs, ogr.wkbPolygon)
    if layer.GetFeatureCount() == 0:
        geometry = ogr.CreateGeometryFromWkt(bbox.get_wkt())
        feature_defn = layer.GetLayerDefn()
        feature = ogr.Feature(feature_defn)
        feature.SetGeometry(geometry)
        layer.CreateFeature(feature)
        feature = None
    layer, datasource = None, None
    return gpkg_path
