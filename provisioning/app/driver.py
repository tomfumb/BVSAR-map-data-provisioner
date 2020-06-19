import argparse
import logging
import sys
import os

from gdal import ConfigurePythonLogging, UseExceptions

from provisioning.app.common.bbox import BBOX
from provisioning.app.sources.bc_hillshade import provision as bc_hillshade_provisioner, OUTPUT_CRS_CODE as bc_hillshade_crs_code, OUTPUT_TYPE as bc_hillshade_output_type
from provisioning.app.sources.bc_resource_roads import provision as bc_resource_roads_provisioner, OUTPUT_CRS_CODE as bc_resource_roads_crs_code, OUTPUT_TYPE as bc_resource_roads_output_type
from provisioning.app.sources.bc_topo_20000 import provision as bc_topo_20000_provisioner, OUTPUT_CRS_CODE as bc_topo_crs_code, OUTPUT_TYPE as bc_topo_output_type
from provisioning.app.sources.canvec_wms import provision as canvec_wms_provisioner, OUTPUT_CRS_CODE as canvec_crs_code, OUTPUT_TYPE as canvec_output_type
from provisioning.app.sources.shelters import provision as shelters_provisioner, OUTPUT_CRS_CODE as shelters_crs_code, OUTPUT_TYPE as shelters_output_type
from provisioning.app.sources.trails import provision as trails_provisioner, OUTPUT_CRS_CODE as trails_crs_code, OUTPUT_TYPE as trails_output_type
from provisioning.app.tilemill.api_client import create_or_update_project
from provisioning.app.tilemill.ProjectLayer import ProjectLayer
from provisioning.app.tilemill.ProjectProperties import ProjectProperties
from provisioning.app.util import get_style_path

UseExceptions()

parser = argparse.ArgumentParser()
parser.add_argument('min_x', type = float)
parser.add_argument('min_y', type = float)
parser.add_argument('max_x', type = float)
parser.add_argument('max_y', type = float)
args = vars(parser.parse_args())

# logDirectory = os.path.join(projectDirectory, 'log')
# os.makedirs(logDirectory, exist_ok = True)
requestedLogLevel = os.environ.get("LOG_LEVEL", "info")
logLevelMapping = {
    "debug": logging.DEBUG,
    "info":  logging.INFO,
    "warn":  logging.WARN,
    "error": logging.ERROR
}
handlers = [
    logging.StreamHandler(stream = sys.stdout),
    # logging.FileHandler(os.path.join(logDirectory, '{nowTs}.log'.format(nowTs = str(int(datetime.datetime.now().timestamp())))))
]
logging.basicConfig(handlers = handlers, level = logLevelMapping.get(requestedLogLevel, logging.INFO), format = '%(levelname)s %(asctime)s %(message)s')
ConfigurePythonLogging(logging.getLogger().name, logging.getLogger().level == logging.DEBUG)

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
create_or_update_project(os.environ.get("TILEMILL_URL", "http://localhost:20009"), ProjectProperties(
    layers=layers,
    mss=mss,
    bbox=bbox,
    zoom_min=6,
    zoom_max=17,
    name="default"
))
