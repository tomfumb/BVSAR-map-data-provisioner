import logging
from api.settings import API_LOG_DIR
from osgeo.gdal import ConfigurePythonLogging, UseExceptions
import os
import sys

from hashlib import md5
from json import dumps


def get_name_for_bounds(
    prefix: str, x_min: float, y_min: float, x_max: float, y_max: float
) -> str:
    return f"{prefix}-{md5(dumps([x_min, y_min, x_max, y_max]).encode('UTF-8')).hexdigest()}"


def configure_logging():
    requestedLogLevel = os.environ.get("LOG_LEVEL", "info")
    logLevelMapping = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warn": logging.WARN,
        "error": logging.ERROR,
    }
    handlers = [
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler(
            filename=os.path.join(API_LOG_DIR, f"api-{os.getpid()}.log"), mode="w"
        ),
    ]
    logging.basicConfig(
        handlers=handlers,
        level=logLevelMapping.get(requestedLogLevel, logging.INFO),
        format="%(levelname)s %(asctime)s %(message)s",
    )

    logger_name = "gdal"
    enable_debug = logging.getLogger().level == logging.DEBUG
    ConfigurePythonLogging(logger_name, enable_debug)
    if not enable_debug:
        # suppress noisy GDAL log output as it is meaningless to most users
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    UseExceptions()
