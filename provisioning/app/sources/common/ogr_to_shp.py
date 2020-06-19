from gdal import ogr
from typing import List

from provisioning.app.common.bbox import BBOX

def ogr_to_shp(
    bbox: BBOX,
    src_layer: ogr.Layer,
    dst_path: str,
    dst_layer_name: str,
    dst_crs_code: str
) -> List[str]:
    src_layer.SetSpatialFilterRect(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
    bbox_driver = ogr.GetDriverByName("ESRI Shapefile")
    bbox_datasource = bbox_driver.CreateDataSource(dst_path)
    bbox_srs = ogr.osr.SpatialReference()
    bbox_srs.ImportFromEPSG(int(dst_crs_code.split(":")[-1]))
    bbox_layer = bbox_datasource.CreateLayer(dst_layer_name, bbox_srs, src_layer.GetLayerDefn().GetGeomType())
    for i in range(src_layer.GetLayerDefn().GetFieldCount()):
        field_defn = src_layer.GetLayerDefn().GetFieldDefn(i)
        bbox_layer.CreateField(field_defn)
    while filtered_feature := src_layer.GetNextFeature():
        bbox_feature = filtered_feature.Clone()
        bbox_geometry = bbox_feature.GetGeometryRef()
        bbox_geometry.TransformTo(bbox_srs)
        bbox_layer.CreateFeature(bbox_feature)

    bbox_datasource = None
    return [dst_path,]