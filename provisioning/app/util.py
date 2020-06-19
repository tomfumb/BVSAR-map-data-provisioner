import os
import shutil

from typing import Final, Tuple

TILEMILL_DATA_LOCATION: Final = "/home/appuser/data"

def get_data_path(path_parts: Tuple[str]) -> str:
    return _get_absolute_path(True, ("data",) + path_parts)

def get_output_path(dir_name: str = None, file_name: str = None) -> str:
    env_var_key: Final = "OUTPUT_LOCATION"
    return _get_absolute_path(not env_var_key in os.environ, (os.environ.get(env_var_key, TILEMILL_DATA_LOCATION), dir_name, file_name))

def get_style_path(file_name: str) -> str:
    return os.path.join(os.path.dirname(__file__), "styles", file_name)

def delete_directory_contents(directory: str) -> str:
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
            raise e

def _get_absolute_path(relative: bool, path_parts: Tuple[str]) -> str:
    if relative:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *path_parts)
    else:
        return os.path.join(*list(filter(lambda part: part, path_parts)))
