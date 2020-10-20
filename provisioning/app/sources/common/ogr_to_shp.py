import json
import logging
from gdal import ogr, osr
from typing import List

from app.common.BBOX import BBOX

def ogr_to_shp(
    bbox: BBOX,
    src_layers: List[ogr.Layer],
    dst_path: str,
    dst_layer_name: str,
    dst_crs_code: str,
) -> List[str]:
    gen_driver = ogr.GetDriverByName("ESRI Shapefile")
    gen_datasource = gen_driver.CreateDataSource(dst_path)
    gen_srs = ogr.osr.SpatialReference()
    gen_srs.ImportFromEPSG(int(dst_crs_code.split(":")[-1]))
    for i, src_layer in enumerate(src_layers):
        if src_layer.GetGeomType() == ogr.wkbNone:
            logging.debug(f"Layer {src_layer.GetName()} does not contain geometries, skipping")
            continue
        src_layer_srs = src_layer.GetSpatialRef()
        clip_geometry = _transform_bbox(bbox, f"{src_layer_srs.GetAuthorityName(None)}:{src_layer_srs.GetAuthorityCode(None)}")
        if i == 0:
            gen_layer = gen_datasource.CreateLayer(dst_layer_name, gen_srs, src_layer.GetLayerDefn().GetGeomType())
            for j in range(src_layer.GetLayerDefn().GetFieldCount()):
                field_defn = src_layer.GetLayerDefn().GetFieldDefn(j)
                gen_layer.CreateField(field_defn)
        src_layer.SetSpatialFilter(clip_geometry)
        logging.debug(f"Clipped src_layer to {src_layer.GetFeatureCount()} features")
        while filtered_feature := src_layer.GetNextFeature():
            contained_feature = filtered_feature.Clone()
            contained_geometry = contained_feature.GetGeometryRef().Intersection(clip_geometry)
            if contained_geometry:
                contained_geometry.AssignSpatialReference(contained_feature.GetGeometryRef().GetSpatialReference()) # geometry loses its spatial ref during Intersection
                contained_geometry.TransformTo(gen_srs)
                contained_feature.SetGeometryDirectly(contained_geometry)
                gen_layer.CreateFeature(contained_feature)

    gen_datasource = None
    return [dst_path,]


def _transform_bbox(bbox: BBOX, target_crs_code: str) -> ogr.Geometry:
    if bbox.crs_code == target_crs_code: return ogr.CreateGeometryFromWkt(bbox.get_wkt())
    srs_in = osr.SpatialReference()
    srs_in.SetFromUserInput(bbox.crs_code)
    srs_out = osr.SpatialReference()
    srs_out.SetFromUserInput(target_crs_code)
    bbox_geom = ogr.CreateGeometryFromWkt(bbox.get_wkt(), srs_in)
    bbox_coords = json.loads(bbox_geom.ExportToJson())
    bbox_coords_transformed = list()
    for bbox_point_pair in bbox_coords["coordinates"][0]:
        point = ogr.Geometry(ogr.wkbPoint)
        point.AssignSpatialReference(srs_in)
        if srs_in.EPSGTreatsAsLatLong() == srs_out.EPSGTreatsAsLatLong():
            point.AddPoint(bbox_point_pair[0], bbox_point_pair[1])
        else:
            point.AddPoint(bbox_point_pair[1], bbox_point_pair[0])
        point.TransformTo(srs_out)
        x, y, _ = point.GetPoint()
        bbox_coords_transformed.append([x, y])
    bbox_coords["coordinates"][0] = bbox_coords_transformed
    bbox_transformed_geom = ogr.CreateGeometryFromJson(json.dumps(bbox_coords))
    bbox_transformed_geom.AssignSpatialReference(srs_out)
    return bbox_transformed_geom
