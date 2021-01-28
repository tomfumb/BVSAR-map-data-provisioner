# prevent infinitely forking processes when multiprocessing is used
if __name__ == "__main__":

    import logging
    import os

    from gdal import ogr, osr
    from typing import List

    from app.common.bbox import BBOX
    from app.bbox_provisioner import provision, ProvisionArg
    from app.common.util import configure_logging
    from app.run_strategy import RunStrategy
    from app.settings import AREAS_PATH

    configure_logging()

    BBOX_DIVISION = float(os.environ.get("BBOX_DIVISION", 0.5))

    datasource = ogr.Open(AREAS_PATH)
    if not datasource:
        logging.error("Could not open {0}. Exiting".format(AREAS_PATH))
        exit(1)

    if datasource.GetLayerCount() != 1:
        logging.error(
            "Expected 1 layer but instead found {0}. Exiting".format(
                datasource.GetLayerCount()
            )
        )
        exit(1)

    def get_profile_names_for_feature(feature: ogr.Feature) -> List[str]:
        return list(
            map(
                lambda profile_names_part: profile_names_part.strip(),
                feature.GetFieldAsString("profile").split(","),
            )
        )

    def get_xyz_url_for_feature(feature: ogr.Feature) -> str:
        return feature.GetFieldAsString("xyz_url")

    provision_args = list()
    area_layer = datasource.GetLayerByIndex(0)
    area_layer.SetAttributeFilter(f"strategy = '{RunStrategy.GRIDDED.value}'")
    while area_feature := area_layer.GetNextFeature():

        def round_for_increment(value: float, increment: float) -> float:
            precision_mulplier = max(int(1 / increment), 0)
            return int(value * precision_mulplier) / precision_mulplier

        grid_min_x, grid_min_y, grid_max_x, grid_max_y = (
            -140,
            47,
            -113,
            61,
        )  # loose bbox for BC with some buffering
        grid_srs = osr.SpatialReference()
        grid_srs.SetFromUserInput("EPSG:4326")
        cell_x_min, walk_increment = (
            grid_min_x,
            float(os.environ.get("GRIDDED_BBOX_INCREMENT", 0.1)),
        )
        while cell_x_min < grid_max_x:
            cell_x_max = round_for_increment(
                cell_x_min + walk_increment, walk_increment
            )
            cell_y_min = grid_min_y
            while cell_y_min < grid_max_y:
                cell_y_max = round_for_increment(
                    cell_y_min + walk_increment, walk_increment
                )
                next_cell_geom = ogr.CreateGeometryFromWkt(
                    f"POLYGON (({cell_x_min} {cell_y_min}, {cell_x_max} {cell_y_min}, {cell_x_max} {cell_y_max}, {cell_x_min} {cell_y_max}, {cell_x_min} {cell_y_min}))"
                )
                next_cell_geom.AssignSpatialReference(grid_srs)
                intersection_geom = area_feature.GetGeometryRef().Intersection(
                    next_cell_geom
                )
                if intersection_geom is not None and not intersection_geom.IsEmpty():
                    provision_args.extend(
                        [
                            ProvisionArg(
                                bbox=BBOX(
                                    min_x=cell_x_min,
                                    min_y=cell_y_min,
                                    max_x=cell_x_max,
                                    max_y=cell_y_max,
                                ),
                                profile_name=profile_name,
                                xyz_url=get_xyz_url_for_feature(area_feature),
                                skippable=int(
                                    os.environ.get("GRIDDED_REPEAT_IF_EXISTS", 0)
                                )
                                != 1,
                            )
                            for profile_name in get_profile_names_for_feature(
                                area_feature
                            )
                        ]
                    )
                cell_y_min = cell_y_max
            cell_x_min = cell_x_max

    area_layer.SetAttributeFilter(f"strategy = '{RunStrategy.ENVELOPE.value}'")
    while area_feature := area_layer.GetNextFeature():
        min_x, max_x, min_y, max_y = area_feature.GetGeometryRef().GetEnvelope()
        reset_y = min_y
        while min_x < max_x:
            increment_x = min(BBOX_DIVISION, max_x - min_x)
            min_y = reset_y
            while min_y < max_y:
                increment_y = min(BBOX_DIVISION, max_y - min_y)
                this_max_x = min_x + increment_x
                this_max_y = min_y + increment_y
                provision_args.extend(
                    [
                        ProvisionArg(
                            bbox=BBOX(
                                min_x=min_x,
                                min_y=min_y,
                                max_x=this_max_x,
                                max_y=this_max_y,
                            ),
                            profile_name=profile_name,
                            xyz_url=get_xyz_url_for_feature(area_feature),
                            skippable=False,
                        )
                        for profile_name in get_profile_names_for_feature(area_feature)
                    ]
                )
                min_y += increment_y
            min_x += increment_x

    for provision_arg in provision_args:
        provision(provision_arg)
