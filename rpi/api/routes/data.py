from os import path, makedirs
from typing import Callable
from fastapi import APIRouter
from osgeo import ogr, osr
from enum import Enum
from api.settings import FILES_DIR, FILES_PATH, SRCDATA_PATH
from hashlib import md5
from json import dumps
from pydantic import BaseModel


bbox_crs: str = "EPSG:4326"
result_dir: str = "src-data-export"
result_dir_path = path.join(FILES_DIR, result_dir)
makedirs(result_dir_path, exist_ok=True)
id_field_name: str = "id"
title_field_name: str = "title"
title_field_width: int = 100
result_layer_name: str = "result_layer"


class Dataset(str, Enum):
    resource_roads = "resource_roads"


class Handler(BaseModel):
    data_retriever: Callable[[ogr.Layer, float, float, float, float], None]
    feature_type: int


def get_features_from_layer(
    source_layer: ogr.Layer,
    destination_layer: ogr.Layer,
    title_provider: Callable[[ogr.Feature], str],
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float
) -> None:
    memory_driver = ogr.GetDriverByName("Memory")
    clip_datasource = memory_driver.CreateDataSource("")
    clip_layer = clip_datasource.CreateLayer("clip_layer", geom_type=ogr.wkbPolygon)
    clip_geom = ogr.CreateGeometryFromWkt(
        f"POLYGON (({x_min} {y_min}, {x_max} {y_min}, {x_max} {y_max}, {x_min} {y_max}, {x_min} {y_min}))"
    )
    clip_srs = osr.SpatialReference()
    clip_srs.SetFromUserInput(bbox_crs)
    clip_geom.AssignSpatialReference(clip_srs)
    feature_defn = clip_layer.GetLayerDefn()
    feature = ogr.Feature(feature_defn)
    feature.SetGeometry(clip_geom)
    clip_layer.CreateFeature(feature)

    result_datasource = memory_driver.CreateDataSource("")
    result_layer = result_datasource.CreateLayer("result_layer", geom_type=ogr.wkbMultiLineString)
    ogr.Layer.Clip(source_layer, clip_layer, result_layer)

    id_field = ogr.FieldDefn(id_field_name, ogr.OFTInteger64)
    title_field = ogr.FieldDefn(title_field_name, ogr.OFTString)
    title_field.SetWidth(title_field_width)
    destination_layer.CreateField(id_field)
    destination_layer.CreateField(title_field)
    while feature := result_layer.GetNextFeature():
        geometry_ref = feature.GetGeometryRef()
        new_geometry = geometry_ref.Clone()
        new_feature = ogr.Feature(destination_layer.GetLayerDefn())
        new_feature.SetGeometryDirectly(new_geometry)
        new_feature.SetField(id_field_name, feature.GetFID())
        new_feature.SetField(title_field_name, title_provider(feature)[0:title_field_width])
        destination_layer.CreateFeature(new_feature)


def get_name_for_export(prefix: str, x_min: float, y_min: float, x_max: float, y_max: float) -> str:
    return f"{prefix}-{md5(dumps([x_min, y_min, x_max, y_max]).encode('UTF-8')).hexdigest()}"


def resource_roads_data(result_layer: ogr.Layer, x_min: float, y_min: float, x_max: float, y_max: float) -> None:
    src_driver = ogr.GetDriverByName("OpenFileGDB")
    src_datasource = src_driver.Open(path.join(SRCDATA_PATH, "FTEN_ROAD_SEGMENT_LINES_SVW.gdb"))
    src_layer = src_datasource.GetLayerByIndex(0)


    def title_provider(feature: ogr.Feature) -> str:
        name = feature.GetFieldAsString("MAP_LABEL")
        status = " (retired)" if feature.GetFieldAsString('LIFE_CYCLE_STATUS_CODE') == "RETIRED" else ""
        return f"{name}{status}"

    get_features_from_layer(src_layer, result_layer, title_provider, x_min, y_min, x_max, y_max)


router = APIRouter()
handlers = {
    Dataset.resource_roads: Handler(
        data_retriever=resource_roads_data,
        feature_type=ogr.wkbMultiLineString,
    )
}

# test with http://localhost:9000/data/export/resource_roads/-126.4/54.89/-126.3/54.91
@router.get("/{dataset}/export/{x_min}/{y_min}/{x_max}/{y_max}")
async def export_features(
    dataset: Dataset, x_min: float, y_min: float, x_max: float, y_max: float
) -> str:
    result_driver = ogr.GetDriverByName("GeoJSON")
    result_filename = f"{get_name_for_export(dataset.value, x_min, y_min, x_max, y_max)}.json"
    result_path = path.join(result_dir_path, result_filename)
    if not path.exists(result_path):
        result_datasource = result_driver.CreateDataSource(result_path)
        result_layer = result_datasource.CreateLayer(result_layer_name, geom_type=handlers[dataset].feature_type)
        handlers[dataset].data_retriever(result_layer, x_min, y_min, x_max, y_max)

    return f"{FILES_PATH}/{result_dir}/{result_filename}"


# test with http://localhost:9000/data/count/resource_roads/-126.4/54.89/-126.3/54.91
@router.get("/{dataset}/count/{x_min}/{y_min}/{x_max}/{y_max}")
async def export_features(
    dataset: Dataset, x_min: float, y_min: float, x_max: float, y_max: float
) -> int:
    result_driver = ogr.GetDriverByName("Memory")
    result_datasource = result_driver.CreateDataSource("")
    result_layer = result_datasource.CreateLayer(result_layer_name, geom_type=handlers[dataset].feature_type)
    handlers[dataset].data_retriever(result_layer, x_min, y_min, x_max, y_max)
    
    return result_layer.GetFeatureCount()