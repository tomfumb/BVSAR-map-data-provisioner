import argparse
import logging
import mbutil
import uuid
import sys
import os
import subprocess

from gdal import ConfigurePythonLogging, UseExceptions
from PIL import Image
from shutil import copyfile, move, rmtree

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.file import remove_intermediaries
from provisioning.app.sources.bc_hillshade import provision as bc_hillshade_provisioner, OUTPUT_CRS_CODE as bc_hillshade_crs_code, OUTPUT_TYPE as bc_hillshade_output_type
from provisioning.app.sources.bc_resource_roads import provision as bc_resource_roads_provisioner, OUTPUT_CRS_CODE as bc_resource_roads_crs_code, OUTPUT_TYPE as bc_resource_roads_output_type
from provisioning.app.sources.bc_topo_20000 import provision as bc_topo_20000_provisioner, OUTPUT_CRS_CODE as bc_topo_crs_code, OUTPUT_TYPE as bc_topo_output_type
from provisioning.app.sources.canvec_wms import provision as canvec_wms_provisioner, OUTPUT_CRS_CODE as canvec_crs_code, OUTPUT_TYPE as canvec_output_type
from provisioning.app.sources.shelters import provision as shelters_provisioner, OUTPUT_CRS_CODE as shelters_crs_code, OUTPUT_TYPE as shelters_output_type
from provisioning.app.sources.trails import provision as trails_provisioner, OUTPUT_CRS_CODE as trails_crs_code, OUTPUT_TYPE as trails_output_type
from provisioning.app.sources.xyz_service import provision as xyz_provisioner, get_output_dir as xyz_get_output_dir
from provisioning.app.tilemill.api_client import create_or_update_project, request_export
from provisioning.app.tilemill.ProjectLayer import ProjectLayer
from provisioning.app.tilemill.ProjectCreationProperties import ProjectCreationProperties
from provisioning.app.tilemill.ProjectProperties import ProjectProperties
from provisioning.app.util import get_style_path, get_export_path, get_result_path, merge_dirs, silent_delete, get_run_data_path, delete_directory_contents


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
parser.add_argument('xyz_url', type = str)
args = vars(parser.parse_args())

run_id = str(uuid.uuid4())
bbox = BBOX(min_x=args["min_x"], min_y=args["min_y"], max_x=args["max_x"], max_y=args["max_y"])

zooms_main = list(range(6, 18)) # range stops 1 short, so 17 is max zoom
zooms_xyz = list(range(16, 18))
layers = list()
for scale, files in canvec_wms_provisioner(bbox, (10000000, 4000000, 2000000, 1000000, 500000, 250000, 150000, 70000, 35000), run_id).items():
    layers.extend([ProjectLayer(path=file, style_class=f"canvec-{scale}", crs_code=canvec_crs_code, type=canvec_output_type) for file in files])
layers.extend([ProjectLayer(path=file, style_class="bc-topo-20000", crs_code=bc_topo_crs_code, type=bc_topo_output_type) for file in bc_topo_20000_provisioner(bbox, run_id)])
layers.extend([ProjectLayer(path=file, style_class="bc-hillshade", crs_code=bc_hillshade_crs_code, type=bc_hillshade_output_type) for file in bc_hillshade_provisioner(bbox, run_id)])
bc_resource_road_files = bc_resource_roads_provisioner(bbox, run_id)
for class_name in ("bc-resource-roads", "bc-resource-roads-label"):
    layers.extend([ProjectLayer(path=bc_resource_road_files[0], style_class=class_name, crs_code=bc_resource_roads_crs_code, type=bc_resource_roads_output_type)])
layers.extend([ProjectLayer(path=trails_provisioner(bbox, run_id)[0], style_class="trails", crs_code=trails_crs_code, type=trails_output_type)])
layers.extend([ProjectLayer(path=shelters_provisioner(bbox, run_id)[0], style_class="shelters", crs_code=shelters_crs_code, type=shelters_output_type)])
    
with open(get_style_path("default.mss"), "r") as f:
    mss = f.read()

project_name = "hybrid"
project_result_path = get_result_path((project_name,))
tilemill_url = os.environ.get("TILEMILL_URL", "http://localhost:20009")
project_properties = ProjectProperties(
    bbox=bbox,
    zoom_min=zooms_main[0],
    zoom_max=zooms_main[-1:][0],
    name=project_name
)
project_creation_properties = ProjectCreationProperties(
    layers=layers,
    mss=mss,
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
xyz_paths = xyz_provisioner(bbox, xyz_url_template, zooms_xyz[0], zooms_xyz[-1:][0], "image/jpeg", "png")
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
        copyfile(xyz_path, xyz_result_path)

if remove_intermediaries():
    rmtree(get_run_data_path(run_id, None))
logging.info("Finished")
