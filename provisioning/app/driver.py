import argparse
import logging
import sys
import os

from gdal import ConfigurePythonLogging, UseExceptions

from provisioning.app.common.bbox import BBOX
from provisioning.app.sources.bc_hillshade import provision as bc_hillshade_provisioner
from provisioning.app.sources.bc_topo_20000 import provision as bc_topo_20000_provisioner
from provisioning.app.sources.canvec_wms import provision as canvec_wms_provisioner

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
bc_topo_20000_provisioner(bbox)
bc_hillshade_provisioner(bbox)
canvec_wms_provisioner(bbox, (
    10000000,
    4000000,
    2000000,
    1000000,
    500000,
    250000,
    150000,
    70000,
    35000,
    20000
))
