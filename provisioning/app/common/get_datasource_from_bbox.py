import os

from gdal import ogr, osr
from typing import Final

from provisioning.app.common.bbox import BBOX

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
    srs.SetFromUserInput(bbox.CRS_CODE)
    if not layer:
        layer = datasource.CreateLayer(BBOX_LAYER_NAME, srs, ogr.wkbPolygon)
    if layer.GetFeatureCount() == 0:
        geometry = ogr.CreateGeometryFromWkt(get_wkt_from_bbox(bbox))
        feature_defn = layer.GetLayerDefn()
        feature = ogr.Feature(feature_defn)
        feature.SetGeometry(geometry)
        layer.CreateFeature(feature)
        feature = None
    layer, datasource = None, None
    return gpkg_path

def get_wkt_from_bbox(bbox: BBOX) -> str:
    return f"POLYGON (({bbox.min_x} {bbox.min_y},{bbox.max_x} {bbox.min_y},{bbox.max_x} {bbox.max_y},{bbox.min_x} {bbox.max_y},{bbox.min_x} {bbox.min_y}))"
