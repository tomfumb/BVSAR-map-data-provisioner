import argparse
import logging
import os
import sys

from gdal import ogr, ConfigurePythonLogging, UseExceptions

from app.common.bbox import BBOX
from app.driver import provision

requestedLogLevel = os.environ.get("LOG_LEVEL", "info")
logLevelMapping = {
    "debug": logging.DEBUG,
    "info":  logging.INFO,
    "warn":  logging.WARN,
    "error": logging.ERROR
}
handlers = [logging.StreamHandler(stream = sys.stdout),]
logging.basicConfig(handlers = handlers, level = logLevelMapping.get(requestedLogLevel, logging.INFO), format = '%(levelname)s %(asctime)s %(message)s')

ConfigurePythonLogging(logging.getLogger().name, logging.getLogger().level == logging.DEBUG)
UseExceptions()

BBOX_DIVISION = float(os.environ.get("BBOX_DIVISION", 0.5))

parser = argparse.ArgumentParser()
parser.add_argument("areas", type = str)
args = vars(parser.parse_args())

if not os.path.exists(args["areas"]):
    logging.error("{0} does not exist. Exiting".format(args["areas"]))
    exit(1)

datasource = ogr.Open(args["areas"])
if not datasource:
    logging.error("Could not open {0}. Exiting".format(args["areas"]))
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
    reset_y = min_y
    while min_x < max_x:
        increment_x = min(BBOX_DIVISION, max_x - min_x)
        min_y = reset_y
        while min_y < max_y:
            increment_y = min(BBOX_DIVISION, max_y - min_y)
            area_division_args.append((
                min_x,
                min_x + increment_x,
                min_y,
                min_y + increment_y,
                profile_name,
                xyz_url,
            ))
            min_y += increment_y
        min_x += increment_x

logging.info(f"Require {len(area_division_args)} export(s) at {BBOX_DIVISION}x{BBOX_DIVISION}")
for idx, args in enumerate(area_division_args):
    logging.info(f"Export {idx + 1} of {len(area_division_args)}")
    provision(BBOX(min_x=args[0], max_x=args[1], min_y=args[2], max_y=args[3]), args[4], args[5])
