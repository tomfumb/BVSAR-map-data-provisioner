import os

from gdal import ogr, osr

from app.common.bbox import BBOX

def record_run(result_dir: str, profile_name: str, bbox: BBOX) -> None:
    layer_name = f"{profile_name}_tiles"
    driver = ogr.GetDriverByName("KML")
    kml_path = os.path.join(result_dir, f"{profile_name}.kml")
    datasource = driver.Open(kml_path)
    if not datasource:
        datasource = driver.CreateDataSource(kml_path)
    layer = datasource.GetLayerByName(layer_name)
    if not layer:
        srs = osr.SpatialReference()
        srs.SetFromUserInput("CRS:84")
        layer = datasource.CreateLayer(layer_name, srs, ogr.wkbPolygon)
    geometry = ogr.CreateGeometryFromWkt(bbox.get_wkt())
    feature_defn = layer.GetLayerDefn()
    feature = ogr.Feature(feature_defn)
    feature.SetGeometry(geometry)
    layer.CreateFeature(feature)
    feature = None
    layer, datasource = None, None
