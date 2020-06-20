import argparse
import logging
import mbutil
import uuid
import sys
import os
import subprocess

from gdal import ConfigurePythonLogging, UseExceptions

from provisioning.app.common.bbox import BBOX
from provisioning.app.common.file import remove_intermediaries
from provisioning.app.sources.bc_hillshade import provision as bc_hillshade_provisioner, OUTPUT_CRS_CODE as bc_hillshade_crs_code, OUTPUT_TYPE as bc_hillshade_output_type
from provisioning.app.sources.bc_resource_roads import provision as bc_resource_roads_provisioner, OUTPUT_CRS_CODE as bc_resource_roads_crs_code, OUTPUT_TYPE as bc_resource_roads_output_type
from provisioning.app.sources.bc_topo_20000 import provision as bc_topo_20000_provisioner, OUTPUT_CRS_CODE as bc_topo_crs_code, OUTPUT_TYPE as bc_topo_output_type
from provisioning.app.sources.canvec_wms import provision as canvec_wms_provisioner, OUTPUT_CRS_CODE as canvec_crs_code, OUTPUT_TYPE as canvec_output_type
from provisioning.app.sources.shelters import provision as shelters_provisioner, OUTPUT_CRS_CODE as shelters_crs_code, OUTPUT_TYPE as shelters_output_type
from provisioning.app.sources.trails import provision as trails_provisioner, OUTPUT_CRS_CODE as trails_crs_code, OUTPUT_TYPE as trails_output_type
from provisioning.app.sources.xyz_service import provision as xyz_provisioner
from provisioning.app.tilemill.api_client import create_or_update_project, request_export
from provisioning.app.tilemill.ProjectLayer import ProjectLayer
from provisioning.app.tilemill.ProjectCreationProperties import ProjectCreationProperties
from provisioning.app.tilemill.ProjectProperties import ProjectProperties
from provisioning.app.util import get_style_path, get_export_path, get_result_path, delete_directory_contents, merge_dirs


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
args = vars(parser.parse_args())

bbox = BBOX(**args)
layers = list()
for scale, files in canvec_wms_provisioner(bbox, (10000000, 4000000, 2000000, 1000000, 500000, 250000, 150000, 70000, 35000, 20000)).items():
    layers.extend([ProjectLayer(path=file, style_class=f"canvec-{scale}", crs_code=canvec_crs_code, type=canvec_output_type) for file in files])
layers.extend([ProjectLayer(path=file, style_class="bc-topo-20000", crs_code=bc_topo_crs_code, type=bc_topo_output_type) for file in bc_topo_20000_provisioner(bbox)])
layers.extend([ProjectLayer(path=file, style_class="bc-hillshade", crs_code=bc_hillshade_crs_code, type=bc_hillshade_output_type) for file in bc_hillshade_provisioner(bbox)])
bc_resource_road_files = bc_resource_roads_provisioner(bbox)
for class_name in ("bc-resource-roads", "bc-resource-roads-label"):
    layers.extend([ProjectLayer(path=bc_resource_road_files[0], style_class=class_name, crs_code=bc_resource_roads_crs_code, type=bc_resource_roads_output_type)])
layers.extend([ProjectLayer(path=trails_provisioner(bbox)[0], style_class="trails", crs_code=trails_crs_code, type=trails_output_type)])
layers.extend([ProjectLayer(path=shelters_provisioner(bbox)[0], style_class="shelters", crs_code=shelters_crs_code, type=shelters_output_type)])
    
with open(get_style_path("default.mss"), "r") as f:
    mss = f.read()

project_name = "default"
tilemill_url = os.environ.get("TILEMILL_URL", "http://localhost:20009")
project_properties = ProjectProperties(
    bbox=bbox,
    zoom_min=6,
    zoom_max=17,
    name=project_name
)
project_creation_properties = ProjectCreationProperties(
    layers=layers,
    mss=mss,
    **dict(project_properties)
)
create_or_update_project(tilemill_url, project_creation_properties)
export_file = request_export(tilemill_url, project_properties)
result_dir_temp = get_result_path((str(uuid.uuid4()),))
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
merge_dirs(result_dir_temp, get_result_path((project_name,)))

xyz_dir = xyz_provisioner(bbox, "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}", "image/jpeg", 6, 17)

logging.info("Finished")
