import requests
import logging
import xml.etree.ElementTree as ET

from provisioners.validators.bboxArgsValidator import bboxArgsValidator

def wmsTileProvisioner(sourceConfig, args, environmentConfig):
    bboxArgsValidator(args)
    wmsConfig = sourceConfig.get('wms')
    logging.debug(str(getWmsParametersFromXml(
        getGetCapabilitiesXml(wmsConfig.get('baseUrl'), wmsConfig.get('version', '1.3.0'))
    )))
    

def getWmsParametersFromXml(xml):
    parameters = {}
    tree = ET.fromstring(xml)
    ns = {'p': 'http://www.opengis.net/wms'}
    defaultMaxDimension = 4096
    maxWidthElement, maxHeightElement = tree.find('./p:Service/p:MaxWidth', ns), tree.find('./p:Service/p:MaxHeight', ns)
    if maxWidthElement == None or maxHeightElement == None:
       logging.warn('Cannot determine WMS\'s max image width or height, defaulting to %d', defaultMaxDimension)
    parameters['maxWidth'] = int(maxWidthElement.text) if maxWidthElement != None else defaultMaxDimension
    parameters['maxHeight'] = int(maxHeightElement.text) if maxHeightElement != None else defaultMaxDimension
    # At this point we could do a bunch of validation, checking the source config against what the WMS permits. For example:
        # Is the requested image format available?
        # Does the bounding box of the requested layer(s) intersect the provided bbox?
        # Is the requested layer(s) available in the requested CRS?
    # These checks are not considered necessary at this time, as data sources are configured in advance and distributed with the tool.
    # Any errors communicating with the WMS based on source config should be caught by the developer.
    # If, at some point, source config is entirely provided by the user at runtime it might be necessary to revisit this.
    return parameters


def getGetCapabilitiesXml(baseUrl, version):
    logging.info('retrieving WMS capabilities XML from %s', baseUrl)
    return requests.get('{baseUrl}?service=WMS&request=GetCapabilities&version={version}'.format(baseUrl = baseUrl, version = version)).text
