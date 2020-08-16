import argparse
import logging
import uuid
import sys
import os
import re
import subprocess

from gdal import ConfigurePythonLogging, UseExceptions
from shutil import copyfile, move, rmtree

from app.common.BBOX import BBOX
from app.common.httpRetriever import check_exists
from app.merging.merge_xyz_tiles import merge_xyz_tiles
from app.profiles.hybrid import get_profile as profile_hybrid
from app.profiles.xyzplus import get_profile as profile_xyzplus
from app.record.run_recorder import record_run
from app.sources.xyz_service import provision as xyz_provisioner, get_output_dir as xyz_get_output_dir, build_exists_check_requests as xyz_check_builder
from app.tilemill.api_client import create_or_update_project, request_export
from app.tilemill.ProjectLayer import ProjectLayer
from app.tilemill.ProjectCreationProperties import ProjectCreationProperties
from app.tilemill.ProjectProperties import ProjectProperties
from app.common.util import get_style_path, get_export_path, get_result_path, merge_dirs, silent_delete, get_run_data_path, delete_directory_contents, configure_logging, remove_intermediaries


def provision(bbox: BBOX, profile_name: str, xyz_url: str) -> None:
    run_id = str(uuid.uuid4())
    profiles = {
        "hybrid": profile_hybrid,
        "xyzplus": profile_xyzplus,
    }
    try:
        profile = profiles[profile_name](bbox, run_id)
    except KeyError:
        logging.error(f"Requested profile {profile_name} does not exist")
        return
    final_result_path = get_result_path((profile_name,))
    layers = [item for sublist in [provisioner() for provisioner in profile.provisioners] for item in sublist]
    stylesheets = list()
    for stylesheet in profile.stylesheets:
        with open(get_style_path(f"{stylesheet}.mss"), "r") as f:
            stylesheets.append(f.read())
    project_properties = ProjectProperties(
        bbox=bbox,
        zoom_min=profile.zoom_min,
        zoom_max=profile.zoom_max,
        name=profile_name
    )
    project_creation_properties = ProjectCreationProperties(
        layers=layers,
        mss=stylesheets,
        **dict(project_properties)
    )
    tilemill_url = os.environ.get("TILEMILL_URL", "http://localhost:20009")

    create_or_update_project(tilemill_url, project_creation_properties)
    export_file = request_export(tilemill_url, project_properties)
    result_dir_temp = get_result_path((run_id,))
    logging.info("Calling mb-util")
    _, stderr = subprocess.Popen([os.environ["MBUTIL_LOCATION"], get_export_path((export_file,)), result_dir_temp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
    if stderr:
        for line in stderr.decode("ascii").split(os.linesep):
            logging.warn(line)
    logging.info("mb-util complete")
    if remove_intermediaries():
        delete_directory_contents(get_export_path())

    if profile.has_xyz():
        xyz_paths = xyz_provisioner(bbox, xyz_url, profile.zoom_xyz_min, profile.zoom_xyz_max, "image/jpeg", "png")
        xyz_path_base = xyz_get_output_dir(xyz_url)
        def get_result_path_for_xyz(xyz_path: str) -> str: return xyz_path.replace(xyz_path_base, final_result_path)
        logging.info("Deleting result tiles that will be overwritten by xyz content")
        for xyz_path in xyz_paths:
            silent_delete(get_result_path_for_xyz(xyz_path))
    else:
        xyz_paths = list()

    logging.info("Searching existing tiles for edge overlaps and merging if necessary")
    edge_tiles = list()
    zooms_to_merge = range(profile.zoom_min, profile.zoom_xyz_min if profile.has_xyz() else profile.zoom_max + 1)
    for zoom_dir in [entry_name for entry_name in os.listdir(result_dir_temp) if os.path.isdir(os.path.join(result_dir_temp, entry_name)) and int(entry_name) in zooms_to_merge]:
        x_dirs = list(map(lambda x_dir: str(x_dir), sorted([int(z_entry) for z_entry in os.listdir(os.path.join(result_dir_temp, zoom_dir))])))
        edge_tiles += list(map(lambda y_file: os.path.join(zoom_dir, x_dirs[0], y_file), os.listdir(os.path.join(result_dir_temp, zoom_dir, x_dirs[0]))))
        if len(x_dirs) > 1:
            edge_tiles += list(map(lambda y_file: os.path.join(zoom_dir, x_dirs[-1], y_file), os.listdir(os.path.join(result_dir_temp, zoom_dir, x_dirs[-1]))))
            if len(x_dirs) > 2:
                for x_mid_dir in list(map(lambda x_dir_num: str(x_dir_num), range(int(x_dirs[1]), int(x_dirs[-1])))):
                    y_file_nums = sorted([int(re.sub(r"\.png", "", y_file_name)) for y_file_name in os.listdir(os.path.join(result_dir_temp, zoom_dir, x_mid_dir))])
                    edge_tiles.append(os.path.join(zoom_dir, x_mid_dir, f"{y_file_nums[0]}.png"))
                    if len(y_file_nums) > 1:
                        edge_tiles.append(os.path.join(zoom_dir, x_mid_dir, f"{y_file_nums[-1]}.png"))
    existing_edge_tiles = [edge_tile for edge_tile in edge_tiles if os.path.exists(os.path.join(final_result_path, edge_tile))]
    for idx, edge_tile in enumerate(existing_edge_tiles):
        logging.info(f"Merging edge tile {idx + 1} of {len(existing_edge_tiles)} to prior output {edge_tile}")
        new_edge_tile_path = os.path.join(result_dir_temp, edge_tile)
        merge_xyz_tiles(os.path.join(final_result_path, edge_tile), new_edge_tile_path, new_edge_tile_path)

    logging.info("Updating result directories with latest export")
    merge_dirs(result_dir_temp, final_result_path)

    if profile.has_xyz():
        logging.info("Merging and transferring xyz tiles to result dir")
        for idx, xyz_path in enumerate(xyz_paths):
            xyz_result_path = get_result_path_for_xyz(xyz_path)
            log_prefix = f"{idx + 1} of {len(xyz_paths)}"
            log_suffix = f"to {xyz_result_path}"
            if os.path.exists(xyz_result_path):
                logging.info(f"{log_prefix} merge and transfer {log_suffix}")
                merge_xyz_tiles(xyz_path, xyz_result_path, xyz_result_path)
            else:
                logging.info(f"{log_prefix} transfer {log_suffix}")
                xyz_result_dir = os.path.dirname(xyz_result_path)
                os.makedirs(xyz_result_dir, exist_ok=True)
                try:
                    copyfile(xyz_path, xyz_result_path)
                except Exception:
                    pass

    logging.info("Validating result")
    check_exists(
        xyz_check_builder(
            bbox,
            "{0}/{1}/{{z}}/{{x}}/{{y}}.png".format(os.environ.get("HTTP_URL", "http://localhost:8001"), profile_name),
            profile.zoom_xyz_min,
            profile.zoom_xyz_max,
            "image/png",
        )
    )

    record_run(final_result_path, profile_name, bbox)

    if remove_intermediaries():
        rmtree(get_run_data_path(run_id, None))

    logging.info("Finished")

if __name__ == "__main__":
    # has been directly invoked, likely debugging
    configure_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("min_x", type = float)
    parser.add_argument("min_y", type = float)
    parser.add_argument("max_x", type = float)
    parser.add_argument("max_y", type = float)
    parser.add_argument("profile", type = str)
    parser.add_argument("xyz_url", type = str)
    args = vars(parser.parse_args())
    provision(
        BBOX(**{key:value for key, value in args.items() if key in ("min_x", "min_y", "max_x", "max_y")}),
        args["profile"],
        args["xyz_url"]
    )
