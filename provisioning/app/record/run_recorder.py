import os

from gdal import ogr, osr

from app.common.bbox import BBOX


def record_run(result_dir: str, profile_name: str, bbox: BBOX) -> None:
    layer_name = "areas"
    gpkg_driver = ogr.GetDriverByName("GPKG")
    gpkg_path = os.path.join(result_dir, "coverage.gpkg")
    gpkg_datasource = gpkg_driver.Open(gpkg_path, 1)
    if not gpkg_datasource:
        gpkg_datasource = gpkg_driver.CreateDataSource(gpkg_path)
    cumulative_layer = gpkg_datasource.GetLayerByName(layer_name)
    if not cumulative_layer:
        srs = osr.SpatialReference()
        srs.SetFromUserInput("CRS:84")
        cumulative_layer = gpkg_datasource.CreateLayer(layer_name, srs, ogr.wkbPolygon)
    geometry = ogr.CreateGeometryFromWkt(bbox.get_wkt())
    feature_defn = cumulative_layer.GetLayerDefn()
    feature = ogr.Feature(feature_defn)
    feature.SetGeometryDirectly(geometry)
    cumulative_layer.CreateFeature(feature)

    kml_path = os.path.join(result_dir, "coverage.kml")
    if os.path.exists(kml_path):
        os.remove(kml_path)
    kml_driver = ogr.GetDriverByName("KML")
    kml_datasource = kml_driver.CreateDataSource(kml_path)
    kml_datasource.CopyLayer(cumulative_layer, "areas")

    geojson_path = os.path.join(result_dir, "coverage.geojson")
    if os.path.exists(geojson_path):
        os.remove(geojson_path)
    geojson_driver = ogr.GetDriverByName("GeoJSON")
    geojson_datasource = geojson_driver.CreateDataSource(geojson_path)
    geojson_datasource.CopyLayer(cumulative_layer, "areas")

    cumulative_layer, gpkg_datasource, kml_datasource, geojson_datasource = (
        None,
        None,
        None,
        None,
    )
