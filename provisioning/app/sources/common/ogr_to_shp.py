from gdal import ogr
from typing import List

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.get_datasource_from_bbox import get_wkt_from_bbox

def ogr_to_shp(
    bbox: BBOX,
    src_layer: ogr.Layer,
    dst_path: str,
    dst_layer_name: str,
    dst_crs_code: str
) -> List[str]:
    src_layer.SetSpatialFilterRect(bbox.min_x, bbox.min_y, bbox.max_x, bbox.max_y)
    gen_driver = ogr.GetDriverByName("ESRI Shapefile")
    gen_datasource = gen_driver.CreateDataSource(dst_path)
    gen_srs = ogr.osr.SpatialReference()
    gen_srs.ImportFromEPSG(int(dst_crs_code.split(":")[-1]))
    gen_layer = gen_datasource.CreateLayer(dst_layer_name, gen_srs, src_layer.GetLayerDefn().GetGeomType())
    bbox_srs = ogr.osr.SpatialReference()
    bbox_srs.ImportFromEPSG(int(bbox.CRS_CODE.split(":")[-1]))
    bbox_geometry = ogr.CreateGeometryFromWkt(get_wkt_from_bbox(bbox), reference=bbox_srs)
    for i in range(src_layer.GetLayerDefn().GetFieldCount()):
        field_defn = src_layer.GetLayerDefn().GetFieldDefn(i)
        gen_layer.CreateField(field_defn)
    while filtered_feature := src_layer.GetNextFeature():
        contained_feature = filtered_feature.Clone()
        contained_geometry = contained_feature.GetGeometryRef().Intersection(bbox_geometry)
        contained_geometry.AssignSpatialReference(contained_feature.GetGeometryRef().GetSpatialReference()) # geometry loses its spatial ref during Intersection
        contained_geometry.TransformTo(gen_srs)
        contained_feature.SetGeometryDirectly(contained_geometry)
        gen_layer.CreateFeature(contained_feature)

    gen_datasource = None
    return [dst_path,]