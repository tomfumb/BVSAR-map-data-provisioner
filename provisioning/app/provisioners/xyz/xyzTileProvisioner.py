import os
import math
import logging

from provisioners.httpRetriever import httpRetriever

from provisioners.validators.bboxArgsValidator import bboxArgsValidator
from provisioners.validators.zoomArgsValidator import zoomArgsValidator

def provision(sourceConfig, stringUserArgs, environmentConfig, projectDirectoryPath):
    bboxArgsValidator(stringUserArgs)
    zoomArgsValidator(stringUserArgs, int(sourceConfig.get('maxAvailableZoom', 20)))
    userArgs = {
        'minX': float(stringUserArgs.get('minX')),
        'minY': float(stringUserArgs.get('minY')),
        'maxX': float(stringUserArgs.get('maxX')),
        'maxY': float(stringUserArgs.get('maxY')),
        'minZ': int(stringUserArgs.get('minZ')),
        'maxZ': int(stringUserArgs.get('maxZ'))
    }
    requests = buildHttpRequestsForGrid(sourceConfig, userArgs, projectDirectoryPath)
    httpRetriever(requests, sourceConfig.get('maxConcurrentRequests'))

def buildHttpRequestsForGrid(sourceConfig, userArgs, projectDirectoryPath):
    requests = list()
    urlTemplate = sourceConfig.get('urlTemplate')
    currentZoom = userArgs.get('minZ')
    while currentZoom <= userArgs.get('maxZ'):
        llTileX, llTileY = deg2num(userArgs.get('minY'), userArgs.get('minX'), currentZoom)
        urTileX, urTileY = deg2num(userArgs.get('maxY'), userArgs.get('maxX'), currentZoom)
        currentX = llTileX
        while currentX <= urTileX:
            currentY = llTileY
            while currentY >= urTileY:
                requests.append({
                    'url': urlTemplate.format(z = currentZoom, x = currentX, y = currentY),
                    'path': os.path.join(projectDirectoryPath, str(currentZoom), str(currentX), '{y}.png'.format(y = currentY)),
                    'expectedType': sourceConfig.get('format', 'image/png')
                })
                currentY -= 1
            currentX += 1
        currentZoom += 1
    return requests

# https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
def deg2num(lat_deg, lon_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)