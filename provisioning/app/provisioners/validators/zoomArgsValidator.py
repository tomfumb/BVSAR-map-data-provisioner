import re
import logging

def zoomArgsValidator(argsDict, maxAvailableZoom, required = True):
    minZoomString = argsDict.get('minZ', None)
    maxZoomString = argsDict.get('maxZ', None)
    logging.debug('validating minZ: %s, maxZ: %s', minZoomString, maxZoomString)

    for stringArg in (minZoomString, maxZoomString):
        if stringArg == None and required:
            logging.warn('Required value(s) not provided for zoom')
            raise ValueError('minZ, maxZ values are all required')
        if re.match(r'^\d{1,2}$', stringArg) == None:
            raise ValueError('Incorrect value format "%s" for zoom. Must be positive integer, 1 or 2 digits', stringArg)
        
    minZoom, maxZoom = float(minZoomString), float(maxZoomString)
    if minZoom > maxZoom:
        raise ValueError('Min zoom cannot exceed max zoom')
    if maxZoom > maxAvailableZoom:
        raise ValueError('Cannot exceed max available zoom (%s)', maxAvailableZoom)