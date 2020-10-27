import os

from gdal import ogr, osr
from typing import Final, List

from app.common.bbox import BBOX


GPKG_DRIVER: Final = ogr.GetDriverByName("GPKG")
LAYER_NAME: Final = "areas"


def _get_gpkg_path(result_dir: str) -> str:
    return os.path.join(result_dir, "coverage.gpkg")


def has_prior_run(result_dir: str, bbox: BBOX) -> bool:
    wkts = [prior_run.get_wkt() for prior_run in get_prior_runs(result_dir)]
    return bbox.get_wkt() in wkts


def get_prior_runs(result_dir: str) -> List[BBOX]:
    path = _get_gpkg_path(result_dir)
    if os.path.exists(path):
        datasource = GPKG_DRIVER.Open(path, 0)
        layer = datasource.GetLayerByName(LAYER_NAME)
        runs = list()
        while area_feature := layer.GetNextFeature():
            run_envelope = area_feature.GetGeometryRef().GetEnvelope()
            runs.append(
                BBOX(
                    min_x=run_envelope[0],
                    min_y=run_envelope[2],
                    max_x=run_envelope[1],
                    max_y=run_envelope[3],
                )
            )
        return runs
    else:
        return list()


def record_run(result_dir: str, bbox: BBOX) -> None:
    gpkg_path = _get_gpkg_path(result_dir)
    gpkg_datasource = GPKG_DRIVER.Open(gpkg_path, 1)
    if not gpkg_datasource:
        gpkg_datasource = GPKG_DRIVER.CreateDataSource(gpkg_path)
    cumulative_layer = gpkg_datasource.GetLayerByName(LAYER_NAME)
    if not cumulative_layer:
        srs = osr.SpatialReference()
        srs.SetFromUserInput("CRS:84")
        cumulative_layer = gpkg_datasource.CreateLayer(LAYER_NAME, srs, ogr.wkbPolygon)
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
