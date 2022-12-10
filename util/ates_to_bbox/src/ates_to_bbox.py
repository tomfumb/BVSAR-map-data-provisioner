from typing import Tuple
from osgeo.ogr import (
    GetDriverByName,
    UseExceptions,
    CreateGeometryFromWkt,
    wkbLineString,
    wkbPolygon,
    wkbMultiPolygon,
    FieldDefn,
    OFTString,
    Feature,
    Geometry,
)
from osgeo.osr import SpatialReference
from os import listdir, environ, path
from json import loads

UseExceptions()

kmz_dir_path = environ["KMZ_DIR_PATH"]
kmz_driver = GetDriverByName("LIBKML")

gpkg_driver = GetDriverByName("GPKG")
gpkg_datasource = gpkg_driver.CreateDataSource(environ["GPKG_PATH"])

memory_driver = GetDriverByName("Memory")
memory_datasource = memory_driver.CreateDataSource("")

gpkg_srs = SpatialReference()
gpkg_srs.ImportFromEPSG(4326)
polygon_layer = memory_datasource.CreateLayer("areas", gpkg_srs, wkbPolygon)
output_layer = gpkg_datasource.CreateLayer("areas", gpkg_srs, wkbPolygon)

profile_field = FieldDefn("profile", OFTString)
xyz_url_field = FieldDefn("xyz_url", OFTString)
strategy_field = FieldDefn("strategy", OFTString)
output_layer.CreateField(profile_field)
output_layer.CreateField(xyz_url_field)
output_layer.CreateField(strategy_field)


def grow_extent(
    minx: float,
    maxx: float,
    miny: float,
    maxy: float,
) -> Tuple[float, float, float, float]:
    """
    OGR's geometry buffer function does not appear to work on unprojected geometries.
    """
    extent_growth_factor = float(environ.get("EXTENT_GROWTH_FACTOR", 0.001))
    return (
        minx - extent_growth_factor,
        maxx + extent_growth_factor,
        miny - extent_growth_factor,
        maxy + extent_growth_factor,
    )


for kmz_file in listdir(kmz_dir_path):
    if kmz_file in loads(environ.get("FILE_BLACKLIST", "[]")):
        continue
    print(f"processing {kmz_file}")
    kmz_file_path = path.join(kmz_dir_path, kmz_file)
    kmz_datasource = kmz_driver.Open(kmz_file_path)
    total_feature_count = 0
    all_layer_extents = None
    for i in range(kmz_datasource.GetLayerCount()):
        layer = kmz_datasource.GetLayerByIndex(i)
        layer_count = layer.GetFeatureCount()
        if layer_count > 0:
            minx, maxx, miny, maxy = layer.GetExtent()
            extent_geom = CreateGeometryFromWkt(
                f"POLYGON (({minx} {miny}, {maxx} {miny}, {maxx} {maxy}, {minx} {maxy}, {minx} {miny}))"
            )
            if all_layer_extents is not None:
                all_layer_extents = all_layer_extents.Union(extent_geom)
            else:
                all_layer_extents = extent_geom
        total_feature_count += layer_count

    if all_layer_extents is not None:
        minx, maxx, miny, maxy = grow_extent(*all_layer_extents.GetEnvelope())
        extent_geom = CreateGeometryFromWkt(
            f"POLYGON (({minx} {miny}, {maxx} {miny}, {maxx} {maxy}, {minx} {maxy}, {minx} {miny}))"
        )
        feature = Feature(polygon_layer.GetLayerDefn())
        feature.SetGeometry(extent_geom)
        polygon_layer.CreateFeature(feature)
    else:
        if total_feature_count != 0:
            raise Exception(
                f"null extent for KMZ {kmz_file} but has {total_feature_count} feature/s"
            )

print("merging overlapping extents")
multipolygon = Geometry(wkbMultiPolygon)
for polygon in polygon_layer:
    if polygon.geometry():
        polygon.geometry().CloseRings()
        wkt = polygon.geometry().ExportToWkt()
        multipolygon.AddGeometryDirectly(CreateGeometryFromWkt(wkt))
union_geometries = multipolygon.UnionCascaded()
for union_geometry in union_geometries:
    feature = Feature(output_layer.GetLayerDefn())
    if union_geometry.GetGeometryType() == wkbLineString:
        polygon = Geometry(wkbPolygon)
        polygon.AddGeometry(union_geometry)
        feature.SetGeometry(polygon)
    elif union_geometry.GetGeometryType() == wkbPolygon:
        feature.SetGeometry(union_geometry)
    else:
        raise Exception(
            f"Unknown geometry type from union {union_geometry.GetGeometryName()}, {union_geometry.GetGeometryType()}"
        )
    feature.SetField("profile", "ates")
    feature.SetFieldNull("xyz_url")
    feature.SetField("strategy", "envelope")
    output_layer.CreateFeature(feature)


print("done")
