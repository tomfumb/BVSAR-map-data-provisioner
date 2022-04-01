from os import environ, path, makedirs
from fastapi import APIRouter
from osgeo import ogr, osr
from enum import Enum
from api.settings import FILES_DIR, UPLOADS_PATH
from uuid import uuid4


bbox_crs: str = "EPSG:4326"
data_output_dirname: str = "src-data-export"

class Dataset(str, Enum):
    resource_roads = "resource_roads"


async def resource_roads_data(x_min: float, y_min: float, x_max: float, y_max: float) -> str:
    src_driver = ogr.GetDriverByName("OpenFileGDB")
    src_datasource = src_driver.Open(path.join(environ.get("SRCDATA_LOCATION", "/www/srcdata"), "FTEN_ROAD_SEGMENT_LINES_SVW.gdb"))
    src_layer = src_datasource.GetLayerByIndex(0)
    clip_driver = ogr.GetDriverByName("Memory")
    clip_datasource = clip_driver.CreateDataSource("")
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

    result_dir_path = path.join(FILES_DIR, data_output_dirname)
    makedirs(result_dir_path, exist_ok=True)
    result_driver = ogr.GetDriverByName("GeoJSON")
    result_filename = f"resource-roads-{str(uuid4())[:6]}.json"
    result_datasource = result_driver.CreateDataSource(path.join(result_dir_path, result_filename))
    result_layer = result_datasource.CreateLayer("result_layer", geom_type=ogr.wkbMultiLineString)
    ogr.Layer.Clip(src_layer, clip_layer, result_layer)

    return f"{UPLOADS_PATH}/{result_filename}"


router = APIRouter()

# test with http://localhost:9000/data/resource_roads/-126.4/54.89/-126.3/54.91
@router.get("/{dataset}/{x_min}/{y_min}/{x_max}/{y_max}")
async def export_info(
    dataset: Dataset, x_min: float, y_min: float, x_max: float, y_max: float
) -> str:
    handlers = {
        Dataset.resource_roads: resource_roads_data,
    }
    return await handlers[dataset](x_min, y_min, x_max, y_max)
