import os

from gdal import ogr
from typing import Final, List

from provisioning.app.common.bbox import BBOX
from provisioning.app.tilemill.ProjectLayerType import ProjectLayerType
from provisioning.app.util import delete_directory_contents, get_data_path, get_output_path

CACHE_DIR_NAME: Final = "bc-resource-roads"
OUTPUT_CRS_CODE: Final = "EPSG:3857"
OUTPUT_TYPE: Final = ProjectLayerType.LINESTRING

def provision(bbox: BBOX) -> List[str]:
    output_dir = get_output_path(CACHE_DIR_NAME)
    os.makedirs(output_dir, exist_ok = True)
    delete_directory_contents(output_dir)
    driver = ogr.GetDriverByName("ESRI Shapefile")
    road_datasource = driver.Open(get_data_path(("FTEN_ROAD_SECTION_LINES_SVW","FTEN_RS_LN_line.shp")))
    road_layer = road_datasource.GetLayerByIndex(0)
    road_layer.SetSpatialFilterRect(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
    bbox_shp_path = get_output_path(CACHE_DIR_NAME, "bbox_roads.shp")
    bbox_datasource = driver.CreateDataSource(bbox_shp_path)
    bbox_srs = ogr.osr.SpatialReference()
    bbox_srs.ImportFromEPSG(int(OUTPUT_CRS_CODE.split(":")[-1]))
    bbox_layer = bbox_datasource.CreateLayer("bbox_roads", bbox_srs, road_layer.GetLayerDefn().GetGeomType())
    for i in range(road_layer.GetLayerDefn().GetFieldCount()):
        field_defn = road_layer.GetLayerDefn().GetFieldDefn(i)
        bbox_layer.CreateField(field_defn)
    while filtered_feature := road_layer.GetNextFeature():
        bbox_feature = filtered_feature.Clone()
        bbox_geometry = bbox_feature.GetGeometryRef()
        bbox_geometry.TransformTo(bbox_srs)
        bbox_layer.CreateFeature(bbox_feature)

    bbox_datasource = None
    return [bbox_shp_path,]
