import glob
import logging
import os
import subprocess

from typing import List
from pydantic import BaseModel

from app.common.BBOX import BBOX
from app.common.util import (
    get_style_path,
    get_result_path,
    get_export_path,
    delete_directory_contents,
    remove_intermediaries,
)
from app.tilemill.api_client import create_or_update_project, request_export
from app.tilemill.ProjectLayer import ProjectLayer
from app.tilemill.ProjectCreationProperties import ProjectCreationProperties
from app.tilemill.ProjectProperties import ProjectProperties


class GenerateResult(BaseModel):
    tile_dir: str
    tile_paths: List[str]


def generate_tiles(
    layers: List[ProjectLayer],
    stylesheets: List[str],
    bbox: BBOX,
    profile_name: str,
    zoom_min: int,
    zoom_max: int,
    run_id: str,
) -> GenerateResult:
    logging.info("Generating tiles from source data")
    stylesheet_content = list()
    for stylesheet in stylesheets:
        with open(get_style_path(f"{stylesheet}.mss"), "r") as f:
            stylesheet_content.append(f.read())
    project_properties = ProjectProperties(
        bbox=bbox, zoom_min=zoom_min, zoom_max=zoom_max, name=profile_name
    )
    if len(layers) > 0:
        project_creation_properties = ProjectCreationProperties(
            layers=layers, mss=stylesheet_content, **dict(project_properties)
        )
        tilemill_url = os.environ.get("TILEMILL_URL", "http://localhost:20009")
        create_or_update_project(tilemill_url, project_creation_properties)
        export_file = request_export(tilemill_url, project_properties)
        result_dir_temp = get_result_path((run_id,))
        logging.info("Calling mb-util")
        _, stderr = subprocess.Popen(
            [
                os.environ["MBUTIL_LOCATION"],
                get_export_path((export_file,)),
                result_dir_temp,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ).communicate()
        if stderr:
            for line in stderr.decode("ascii").split(os.linesep):
                logging.warn(line)
        logging.info("mb-util complete")
        if remove_intermediaries():
            delete_directory_contents(get_export_path())
        return GenerateResult(
            tile_dir=result_dir_temp,
            tile_paths=[
                filename
                for filename in glob.iglob(
                    os.path.join(result_dir_temp, "**", "*.png"), recursive=True
                )
            ],
        )
