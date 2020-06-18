import argparse
import logging
import sys
import os

from gdal import ConfigurePythonLogging, UseExceptions

from provisioning.app.common.bbox import BBOX
from provisioning.app.sources.bc_hillshade import provision as bc_hillshade_provisioner, CACHE_DIR_NAME as bc_hillshade_dir, OUTPUT_CRS_CODE as bc_hillshade_crs_code
from provisioning.app.sources.bc_topo_20000 import provision as bc_topo_20000_provisioner, CACHE_DIR_NAME as bc_topo_dir, OUTPUT_CRS_CODE as bc_topo_crs_code
from provisioning.app.sources.canvec_wms import provision as canvec_wms_provisioner, CACHE_DIR_NAME as canvec_dir, OUTPUT_CRS_CODE as canvec_crs_code
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
    layers.extend([ProjectLayer(path=file, style_class=f"canvec-{scale}", crs_code=canvec_crs_code) for file in files])
layers.extend([ProjectLayer(path=file, style_class="bc-topo-20000", crs_code=bc_topo_crs_code) for file in bc_topo_20000_provisioner(bbox)])
layers.extend([ProjectLayer(path=file, style_class="bc-hillshade", crs_code=bc_hillshade_crs_code) for file in bc_hillshade_provisioner(bbox)])
    
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
