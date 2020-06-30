import argparse
import logging
import uuid
import sys
import os
import subprocess

from gdal import ConfigurePythonLogging, UseExceptions
from PIL import Image
from shutil import copyfile, move, rmtree

from app.common.bbox import BBOX
from app.common.file import remove_intermediaries
from app.profiles.hybrid import get_profile as profile_hybrid
from app.profiles.xyzplus import get_profile as profile_xyzplus
from app.sources.xyz_service import provision as xyz_provisioner, get_output_dir as xyz_get_output_dir
from app.tilemill.api_client import create_or_update_project, request_export
from app.tilemill.ProjectLayer import ProjectLayer
from app.tilemill.ProjectCreationProperties import ProjectCreationProperties
from app.tilemill.ProjectProperties import ProjectProperties
from app.util import get_style_path, get_export_path, get_result_path, merge_dirs, silent_delete, get_run_data_path, delete_directory_contents


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

parser = argparse.ArgumentParser()
parser.add_argument('min_x', type = float)
parser.add_argument('min_y', type = float)
parser.add_argument('max_x', type = float)
parser.add_argument('max_y', type = float)
parser.add_argument('profile', type = str)
parser.add_argument('xyz_url', type = str)
args = vars(parser.parse_args())

run_id = str(uuid.uuid4())
bbox = BBOX(min_x=args["min_x"], min_y=args["min_y"], max_x=args["max_x"], max_y=args["max_y"])
profile_name = args["profile"]

profiles = {
    "hybrid": profile_hybrid,
    "xyzplus": profile_xyzplus
}
try:
    profile = profiles[profile_name](bbox, run_id)
except KeyError:
    logging.error("Requested profile %s does not exist", profile_name)
    exit(1)
 
layers = [item for sublist in [provisioner() for provisioner in profile.provisioners] for item in sublist]

stylesheets = list()
for stylesheet in profile.stylesheets:
    with open(get_style_path(f"{stylesheet}.mss"), "r") as f:
        stylesheets.append(f.read())

project_result_path = get_result_path((profile_name,))
tilemill_url = os.environ.get("TILEMILL_URL", "http://localhost:20009")
project_properties = ProjectProperties(
    bbox=bbox,
    zoom_min=profile.zooms[0],
    zoom_max=profile.zooms[1],
    name=profile_name
)
project_creation_properties = ProjectCreationProperties(
    layers=layers,
    mss=stylesheets,
    **dict(project_properties)
)
create_or_update_project(tilemill_url, project_creation_properties)
export_file = request_export(tilemill_url, project_properties)
result_dir_temp = get_result_path((run_id,))
logging.info("Calling mb-util")
stdout, stderr = subprocess.Popen([os.environ["MBUTIL_LOCATION"], get_export_path((export_file,)), result_dir_temp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
if stdout:
    for line in stdout.decode("ascii").split(os.linesep):
        logging.info(line)
if stderr:
    for line in stderr.decode("ascii").split(os.linesep):
        logging.warn(line)
logging.info("mb-util complete")
if remove_intermediaries():
    delete_directory_contents(get_export_path())

xyz_url_template = args["xyz_url"]
xyz_paths = xyz_provisioner(bbox, xyz_url_template, profile.zooms_xyz[0], profile.zooms_xyz[1], "image/jpeg", "png")
xyz_path_base = xyz_get_output_dir(xyz_url_template)
def get_result_path_for_xyz(xyz_path: str) -> str: return xyz_path.replace(xyz_path_base, project_result_path)
logging.info("Deleting result tiles that will be overwritten by xyz content")
for xyz_path in xyz_paths:
    silent_delete(get_result_path_for_xyz(xyz_path))

logging.info("Updating result directories with latest export")
merge_dirs(result_dir_temp, project_result_path)

logging.info("Merging xyz tiles in result dir")
for xyz_path in xyz_paths:
    xyz_result_path = get_result_path_for_xyz(xyz_path)
    if os.path.exists(xyz_result_path):
        overlay_image = Image.open(xyz_result_path).convert("RGBA")
        base_image = Image.open(xyz_path)
        for i in range(256):
            for j in range(256):
                coord = (i,j)
                values = overlay_image.getpixel(coord)
                if values[3] > 0:
                    base_image.putpixel(coord, values)
        base_image.quantize(method=2).save(xyz_result_path)
    else:
        xyz_result_dir = os.path.dirname(xyz_result_path)
        os.makedirs(xyz_result_dir, exist_ok=True)
        try:
            copyfile(xyz_path, xyz_result_path)
        except Exception:
            pass

if remove_intermediaries():
    rmtree(get_run_data_path(run_id, None))
logging.info("Finished")
