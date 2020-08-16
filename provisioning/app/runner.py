import argparse
import logging
import os
import sys

from gdal import ogr, ConfigurePythonLogging, UseExceptions

from app.common.bbox import BBOX
from app.driver import provision
from app.util import configure_logging

configure_logging()

AREAS_ARG_NAME = "areas"
AREAS_ENV_VAR_NAME = "AREAS_LOCATION"
LOCAL_FEATURES_ARG_NAME = "local-features"
LOCAL_FEATURES_ENV_VAR_NAME = "LOCAL_FEATURES_LOCATION"
BBOX_DIVISION = float(os.environ.get("BBOX_DIVISION", 0.5))

parser = argparse.ArgumentParser()
parser.add_argument(f"--{AREAS_ARG_NAME}", type=str, help=f"Location of {AREAS_ARG_NAME} geopackage, will override {AREAS_ENV_VAR_NAME} env var if present")
parser.add_argument(f"--{LOCAL_FEATURES_ARG_NAME}", type=str, help=f"Location of {LOCAL_FEATURES_ARG_NAME} geopackage, will override {LOCAL_FEATURES_ENV_VAR_NAME} env var if present")
args = vars(parser.parse_args())

areas_path = args.get(AREAS_ARG_NAME) or os.environ.get(AREAS_ENV_VAR_NAME)
local_features_path = args.get(LOCAL_FEATURES_ARG_NAME) or os.environ.get(LOCAL_FEATURES_ENV_VAR_NAME)
error_missing_str = "{0} geopackage must be specified either by {1} or --{0} argument"

if not areas_path:
    logging.error(error_missing_str.format(AREAS_ARG_NAME, AREAS_ENV_VAR_NAME))
    exit(1)

if not local_features_path:
    logging.error(error_missing_str.format(LOCAL_FEATURES_ARG_NAME, LOCAL_FEATURES_ENV_VAR_NAME))
    exit(1)
else:
    # application expects the env var alone to provide this path, so ensure it has the correct value
    os.environ[LOCAL_FEATURES_ENV_VAR_NAME] = local_features_path

datasource = ogr.Open(areas_path)
if not datasource:
    logging.error("Could not open {0}. Exiting".format(areas_path))
    exit(1)

if datasource.GetLayerCount() != 1:
    logging.error("Expected 1 layer but instead found {0}. Exiting".format(datasource.GetLayerCount()))
    exit(1)

def get_bounding_box(geom: ogr.Geometry) -> ogr.Geometry:
    return ogr.CreateGeometryFromWkt(f"POLYGON (({min_x} {min_y},{max_x} {min_y},{max_x} {max_y},{min_x} {max_y},{min_x} {min_y}))")

area_layer = datasource.GetLayerByIndex(0)
area_division_args = list()
while area_feature := area_layer.GetNextFeature():
    profile_name = area_feature.GetFieldAsString("profile")
    xyz_url = area_feature.GetFieldAsString("xyz_url")
    if profile_name is None or profile_name == '' or xyz_url is None or xyz_url == '':
        logging.error(f"profile and xyz_url are required text fields but are missing one or more features. Exiting")
        exit(1)
    min_x, max_x, min_y, max_y = area_feature.GetGeometryRef().GetEnvelope()
    logging.info(f"area {min_x},{min_y} {max_x},{max_y}. x diff: {max_x - min_x}, y diff: {max_y - min_y}")
    reset_y = min_y
    while min_x < max_x:
        increment_x = min(BBOX_DIVISION, max_x - min_x)
        min_y = reset_y
        while min_y < max_y:
            increment_y = min(BBOX_DIVISION, max_y - min_y)
            this_max_x = min_x + increment_x
            this_max_y = min_y + increment_y
            logging.info(f"area division {min_x},{this_max_x} {min_y},{this_max_y}. x diff: {this_max_x - min_x}, y diff: {this_max_y - min_y}")
            area_division_args.append((
                min_x,
                this_max_x,
                min_y,
                this_max_y,
                profile_name,
                xyz_url,
            ))
            min_y += increment_y
        min_x += increment_x

logging.info(f"Require {len(area_division_args)} export(s) at {BBOX_DIVISION}x{BBOX_DIVISION}")
for idx, args in enumerate(area_division_args):
    logging.info(f"Export {idx + 1} of {len(area_division_args)}: {args[0]},{args[2]} {args[1]},{args[3]}")
    provision(BBOX(min_x=args[0], max_x=args[1], min_y=args[2], max_y=args[3]), args[4], args[5])
