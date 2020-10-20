import errno
import logging
import os
import re
import shutil
import sys

from gdal import ConfigurePythonLogging, UseExceptions
from typing import Final, Tuple

TILEMILL_DATA_LOCATION: Final = "/tiledata"
OVERWRITE_EXISTING: Final = int(os.environ.get("OVERWRITE_EXISTING", 0)) == 0

def get_base_path() -> str:
    return os.environ.get("DATA_LOCATION", TILEMILL_DATA_LOCATION)

def get_data_path(path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(os.path.dirname(__file__), "..", "..", "data", *(path_parts if path_parts else list())))

def get_local_features_path() -> str:
    return os.environ["LOCAL_FEATURES_LOCATION"]

def get_cache_path(path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(get_base_path(), "cache", *(path_parts if path_parts else list())))

def get_run_data_path(run_id: str, path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(get_base_path(), "run", run_id, *(path_parts if path_parts else list())))

def get_style_path(file_name: str) -> str:
    return os.path.join(*(os.path.dirname(__file__), "..", "styles", file_name))

def get_export_path(path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(get_base_path(), "export", *(path_parts if path_parts else list())))

def get_result_path(path_parts: Tuple[str] = None) -> str:
    return os.path.join(*(get_base_path(), "result", *(path_parts if path_parts else list())))

def delete_directory_contents(directory: str) -> str:
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logging.warn(f'Failed to delete {file_path}. Reason: {e}')
            raise e

# https://stackoverflow.com/a/10840586/519575
def silent_delete(path: str) -> None:
    try:
        os.remove(path)
    except OSError as e:
        if e.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occurred

# https://unix.stackexchange.com/a/510724/328901
def merge_dirs(source_root: str, dest_root: str) -> None:
    for path, dirs, files in os.walk(source_root, topdown=False):
        dest_dir = os.path.join(
            dest_root,
            os.path.relpath(path, source_root)
        )
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        for filename in files:
            shutil.move(
                os.path.join(path, filename),
                os.path.join(dest_dir, filename)
            )
        for dirname in dirs:
            os.rmdir(os.path.join(path, dirname))
    shutil.rmtree(source_root)

def configure_logging():
    requestedLogLevel = os.environ.get("LOG_LEVEL", "info")
    logLevelMapping = {
        "debug": logging.DEBUG,
        "info":  logging.INFO,
        "warn":  logging.WARN,
        "error": logging.ERROR
    }
    handlers = [logging.StreamHandler(stream = sys.stdout),]
    logging.basicConfig(handlers = handlers, level = logLevelMapping.get(requestedLogLevel, logging.INFO), format = '%(levelname)s %(asctime)s %(message)s')

    logger_name = "gdal"
    enable_debug = logging.getLogger().level == logging.DEBUG
    ConfigurePythonLogging(logger_name, enable_debug)
    if not enable_debug:
        # suppress noisy GDAL log output as it is meaningless to most users
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    UseExceptions()

def swallow_unimportant_warp_error(ex: Exception) -> None:
    if re.match(r"Attempt to create 0x\d+ dataset is illegal\,sizes must be larger than zero", str(ex)):
        logging.debug(f"Bouding box intersects too few pixels to clip a new image")
    else:
        raise ex

def skip_file_creation(path: str) -> bool:
    return os.path.exists(path) and OVERWRITE_EXISTING

def remove_intermediaries() -> bool:
    return int(os.environ.get("REMOVE_INTERMEDIARIES", 1)) == 1
