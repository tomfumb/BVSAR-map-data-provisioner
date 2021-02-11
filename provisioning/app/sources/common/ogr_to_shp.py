import logging
from gdal import ogr
from typing import List

from app.common.bbox import BBOX


def ogr_to_provided(
    bbox: BBOX,
    src_layers: List[ogr.Layer],
    dst_datasource: ogr.DataSource,
    dst_layer_name: str,
    dst_crs_code: str,
):
    ogr_to_ogr(bbox, src_layers, dst_datasource, dst_layer_name, dst_crs_code)


def ogr_to_shp(
    bbox: BBOX,
    src_layers: List[ogr.Layer],
    dst_path: str,
    dst_layer_name: str,
    dst_crs_code: str,
) -> None:
    dst_driver = ogr.GetDriverByName("ESRI Shapefile")
    dst_datasource = dst_driver.CreateDataSource(dst_path)
    ogr_to_ogr(bbox, src_layers, dst_datasource, dst_layer_name, dst_crs_code)
    dst_datasource = None


def ogr_to_ogr(
    bbox: BBOX,
    src_layers: List[ogr.Layer],
    dst_datasource: ogr.DataSource,
    dst_layer_name: str,
    dst_crs_code: str,
) -> None:
    gen_srs = ogr.osr.SpatialReference()
    gen_srs.ImportFromEPSG(int(dst_crs_code.split(":")[-1]))
    for i, src_layer in enumerate(src_layers):
        if src_layer.GetGeomType() == ogr.wkbNone:
            logging.debug(
                f"Layer {src_layer.GetName()} does not contain geometries, skipping"
            )
            continue
        src_layer_srs = src_layer.GetSpatialRef()
        clip_geometry = bbox.transform_as_geom(
            f"{src_layer_srs.GetAuthorityName(None)}:{src_layer_srs.GetAuthorityCode(None)}"
        )
        if i == 0:
            gen_layer = dst_datasource.CreateLayer(
                dst_layer_name, gen_srs, src_layer.GetLayerDefn().GetGeomType()
            )
            for j in range(src_layer.GetLayerDefn().GetFieldCount()):
                field_defn = src_layer.GetLayerDefn().GetFieldDefn(j)
                gen_layer.CreateField(field_defn)
        src_layer.SetSpatialFilter(clip_geometry)
        logging.debug(f"Clipped src_layer to {src_layer.GetFeatureCount()} features")
        while filtered_feature := src_layer.GetNextFeature():
            contained_feature = filtered_feature.Clone()
            contained_geometry = contained_feature.GetGeometryRef().Intersection(
                clip_geometry
            )
            if contained_geometry:
                contained_geometry.AssignSpatialReference(
                    contained_feature.GetGeometryRef().GetSpatialReference()
                )  # geometry loses its spatial ref during Intersection
                contained_geometry.TransformTo(gen_srs)
                contained_feature.SetGeometryDirectly(contained_geometry)
                gen_layer.CreateFeature(contained_feature)
