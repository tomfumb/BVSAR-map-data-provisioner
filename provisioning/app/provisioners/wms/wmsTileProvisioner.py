import requests
import logging
import xml.etree.ElementTree as ET
import ogr
import math
import os

from pyproj import Transformer, CRS

from provisioners.validators.bboxArgsValidator import bboxArgsValidator
from provisioners.httpRetriever import httpRetriever

from provisioners.converters.tiffConverter import tiffConverter

from provisioners.tilemill.tiffProjectManager import generateTilesFromTiff

def provision(sourceConfig, stringUserArgs, environmentConfig, projectDirectoryPath):
    bboxArgsValidator(stringUserArgs)
    userArgs = {
        'minX': float(stringUserArgs.get('minX')),
        'minY': float(stringUserArgs.get('minY')),
        'maxX': float(stringUserArgs.get('maxX')),
        'maxY': float(stringUserArgs.get('maxY'))
    }
    logging.debug('Original source config: %s', str(sourceConfig))
    wmsParameters = getWmsParametersFromXml(getGetCapabilitiesXml(sourceConfig))
    sourceConfig = updateConfigToAvailableLayers(sourceConfig, userArgs, wmsParameters)
    logging.debug('Intersect-filtered source config: %s', str(sourceConfig))
    if len(sourceConfig.get('wms').get('layers')) == 0:
        logging.warn('Requested data source does not intersect requested bbox. Nothing to do')
        exit(0)
    # At this point we could do a bunch more validation, checking the source config against what the WMS permits. For example:
        # Is the requested image format available?
        # Is the requested layer(s) available in the requested CRS?
    # These checks are not considered necessary at this time, as data sources are configured in advance and distributed with the tool.
    # Any errors communicating with the WMS based on source config should be caught by the config developer.
    # If, at some point, source config is entirely provided by the user at runtime it might be necessary to revisit this.
    grid = buildGridForBbox(sourceConfig, userArgs, wmsParameters)
    requests = buildHttpRequestsForGrid(sourceConfig, grid, projectDirectoryPath)
    httpRetriever(requests)
    conversionConfig = sourceConfig.get('conversion')
    if conversionConfig != None:
        conversionType = conversionConfig.get('type')
        logging.debug('Conversion required, type %s', conversionType)
        conversionTypes = {
            'tiff': tiffConverter
        }
        conversionTypes.get(conversionType)(list(map(lambda request: { 'path': request.get('path'), 'bbox': request.get('bbox') }, requests)), sourceConfig.get('crs'))
    generateTilesFromTiff(sourceConfig, userArgs, projectDirectoryPath, environmentConfig, False)


def getGetCapabilitiesXml(sourceConfig):
    wmsConfig = sourceConfig.get('wms')
    url, version = wmsConfig.get('baseUrl'), wmsConfig.get('version', '1.3.0')
    logging.info('retrieving WMS capabilities XML from %s', url)
    return requests.get('{baseUrl}?service=WMS&request=GetCapabilities&version={version}'.format(baseUrl = url, version = version)).text
    

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
    parameters['layers'] = list()
    for namedLayerElement in tree.findall('./p:Capability//p:Layer/[p:Name]', ns):
        namedLayerBboxElement = namedLayerElement.find('./p:EX_GeographicBoundingBox', ns)
        parameters['layers'].append({
            'name': namedLayerElement.find('./p:Name', ns).text,
            'minX': float(namedLayerBboxElement.find('./p:westBoundLongitude', ns).text) if namedLayerBboxElement != None else -180,
            'minY': float(namedLayerBboxElement.find('./p:southBoundLatitude', ns).text) if namedLayerBboxElement != None else -90,
            'maxX': float(namedLayerBboxElement.find('./p:eastBoundLongitude', ns).text) if namedLayerBboxElement != None else 180,
            'maxY': float(namedLayerBboxElement.find('./p:northBoundLatitude', ns).text) if namedLayerBboxElement != None else 90
        })
    return parameters


def updateConfigToAvailableLayers(sourceConfig, userArgs, wmsParameters):
    intersectingLayers = list()
    bboxWktTemplate = 'POLYGON (({minX} {minY}, {maxX} {minY}, {maxX} {maxY}, {minX} {maxY}, {minX} {minY}))'
    bboxWkt = bboxWktTemplate.format(minX = userArgs.get('minX'), minY = userArgs.get('minY'), maxX = userArgs.get('maxX'), maxY = userArgs.get('maxY'))
    bboxExtent = ogr.CreateGeometryFromWkt(bboxWkt)
    logging.debug('Requested bbox WKT: %s', bboxWkt)
    for requiredLayer in sourceConfig.get('wms').get('layers'):
        matchingWmsLayers = list(filter(lambda wmsLayer: wmsLayer.get('name') == requiredLayer.get('name'), wmsParameters.get('layers')))
        if len(matchingWmsLayers) == 1:
            matchingWmsLayer = matchingWmsLayers[0]
            wmsLayerWkt = bboxWktTemplate.format(
                minX = matchingWmsLayer.get('minX'),
                minY = matchingWmsLayer.get('minY'),
                maxX = matchingWmsLayer.get('maxX'),
                maxY = matchingWmsLayer.get('maxY')
            )
            logging.debug('Requested layer %s bbox WKT: %s', matchingWmsLayer.get('name'), wmsLayerWkt)
            wmsLayerExtent = ogr.CreateGeometryFromWkt(wmsLayerWkt)
            intersection = bboxExtent.Intersection(wmsLayerExtent)
            if intersection.GetArea() > 0:
                logging.debug('layer %s does intersect bbox', requiredLayer.get('name'))
                intersectingLayers.append(requiredLayer)
            else:
                logging.debug('layer %s does not intersect bbox', requiredLayer.get('name'))
    newSourceConfig = sourceConfig.copy()
    newSourceConfig.get('wms')['layers'] = intersectingLayers
    return newSourceConfig


def buildGridForBbox(sourceConfig, userArgs, wmsParameters):
    bboxCrs = CRS('EPSG:4326')
    wmsCrs = CRS(sourceConfig.get('crs'))
    transformer = Transformer.from_crs(bboxCrs, wmsCrs, always_xy = True)
    lowerLeft = list(map(lambda ord: math.floor(ord), transformer.transform(userArgs.get('minX'), userArgs.get('minY'))))
    upperRight = list(map(lambda ord: math.ceil(ord), transformer.transform(userArgs.get('maxX'), userArgs.get('maxY'))))
    totalWidthMapUnits = upperRight[0] - lowerLeft[0]
    totalHeightMapUnits = upperRight[1] - lowerLeft[1]
    maxImagePixelWidth, maxImagePixelHeight = wmsParameters.get('maxWidth'), wmsParameters.get('maxHeight')
    dpi = sourceConfig.get('wms').get('dpi', 96)
    scales = sourceConfig.get('tile').get('scales').keys()
    imageRequests = dict()
    for scale in scales:
        imageRequests[scale] = list()
        mapWidthInPixels, mapHeightInPixels = mapUnitsToPixels(totalWidthMapUnits, scale, dpi, wmsCrs), mapUnitsToPixels(totalHeightMapUnits, scale, dpi, wmsCrs)
        maxImageMapUnitWidth, maxImageMapUnitHeight = pixelsToMapUnits(maxImagePixelWidth, scale, dpi, wmsCrs), pixelsToMapUnits(maxImagePixelHeight, scale, dpi, wmsCrs)
        xImageCount, yImageCount = mapWidthInPixels / maxImagePixelWidth, mapHeightInPixels / maxImagePixelHeight
        gridColCount, gridRowCount = math.ceil(xImageCount), math.ceil(yImageCount)
        for i in range(gridColCount):
            pixelWidthThisImage = maxImagePixelWidth if i < gridColCount - 1 or gridColCount == xImageCount else mapWidthInPixels % maxImagePixelWidth
            startX = lowerLeft[0] if i == 0 else imageRequests[scale][-1][-1].get('maxX')
            endX = startX + (maxImageMapUnitWidth if pixelWidthThisImage == maxImagePixelWidth else pixelsToMapUnits(pixelWidthThisImage, scale, dpi, wmsCrs))
            imageRequests[scale].append(list())
            for j in range(gridRowCount):
                pixelHeightThisImage = maxImagePixelHeight if j < gridRowCount - 1 or gridRowCount == yImageCount else mapHeightInPixels % maxImagePixelHeight
                startY = lowerLeft[1] if j == 0 else imageRequests[scale][-1][-1].get('maxY')
                endY = startY + (maxImageMapUnitHeight if pixelHeightThisImage == maxImagePixelHeight else pixelsToMapUnits(pixelHeightThisImage, scale, dpi, wmsCrs))
                imageRequests[scale][-1].append({ 'minX': startX, 'minY': startY, 'maxX': endX, 'maxY': endY, 'width': pixelWidthThisImage, 'height': pixelHeightThisImage })
    return imageRequests


def mapUnitsToPixels(mapUnits, scale, dpi, mapCrs):
    return (mapUnits / scale) / getMapUnitsInOneInch(mapCrs) * dpi


def pixelsToMapUnits(pixels, scale, dpi, mapCrs):
    return ((pixels * scale) / dpi) * getMapUnitsInOneInch(mapCrs)


def getMapUnitsInOneInch(mapCrs):
    metersInOneInch = 0.0254
    mapCrsMetreConversionFactor = mapCrs.axis_info[0].unit_conversion_factor
    return metersInOneInch * mapCrsMetreConversionFactor

def buildHttpRequestsForGrid(sourceConfig, grid, projectDirectoryPath):
    requests = list()
    wmsConfig = sourceConfig.get('wms')
    layers = ','.join(list(map(lambda layer: layer.get('name'), wmsConfig.get('layers'))))
    styles = ','.join(list(map(lambda layer: layer.get('style'), wmsConfig.get('layers'))))
    wmsVersion = sourceConfig.get('wms').get('version')
    for scale in grid:
        i = 0
        for column in grid.get(scale):
            j = 0
            for cell in column:
                url = \
                    '{baseUrl}?'.format(baseUrl = wmsConfig.get('baseUrl')) + \
                    'SERVICE=WMS&' + \
                    'VERSION={version}&'.format(version = wmsVersion) + \
                    'REQUEST=GetMap&' + \
                    'BBOX={minX},{minY},{maxX},{maxY}&'.format(minX = cell.get('minX'), minY = cell.get('minY'), maxX = cell.get('maxX'), maxY = cell.get('maxY')) + \
                    '{crsIdentifier}={epsgCode}&'.format(crsIdentifier = 'SRS' if wmsVersion == '1.1.0' else 'CRS', epsgCode = sourceConfig.get('crs')) + \
                    'WIDTH={width}&HEIGHT={height}&'.format(width = cell.get('width'), height = cell.get('height')) + \
                    'LAYERS={layers}&'.format(layers = layers) + \
                    'STYLES={styles}&'.format(styles = styles) + \
                    'FORMAT=image/{format}&'.format(format = wmsConfig.get('format')) + \
                    'DPI={dpi}&MAP_RESOLUTION={dpi}&FORMAT_OPTIONS=dpi:{dpi}&'.format(dpi = wmsConfig.get('dpi')) + \
                    'TRANSPARENT={transparent}'.format(transparent = True if int(wmsConfig.get('transparent')) == 1 else False)
                requests.append({
                    'path': os.path.join(
                        projectDirectoryPath,
                        str(scale),
                        'col{i}_row{j}.{format}'.format(i = i, j = j, format = wmsConfig.get('format'))
                    ),
                    'url': url,
                    'expectedType': 'image/{format}'.format(format = wmsConfig.get('format')),
                    'bbox': cell
                })
                j = j + 1
            i = i + 1
    return requests