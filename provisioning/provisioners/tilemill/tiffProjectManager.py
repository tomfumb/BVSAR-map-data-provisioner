import os
import re
import ogr
import gdal
import logging
import requests
import subprocess

from pyproj import CRS, Transformer

from provisioners.namers.sourceAndArgNamer import sourceAndArgNamer

from provisioners.tilemill.apiClient import createOrUpdateProject, requestExport

def generateTilesFromTiff(sourceConfig, bounds, projectDirectoryPath, environmentConfig):
    projectDefinition = getProjectDefinition(sourceConfig, bounds, projectDirectoryPath, environmentConfig)
    createOrUpdateProject(projectDefinition, environmentConfig)
    requestExport(bounds, projectDefinition, projectDirectoryPath, environmentConfig)

def getProjectDefinition(sourceConfig, bounds, projectDirectoryPath, environmentConfig):
    session = requests.session()
    projectName = projectDirectoryPath.split(os.path.sep).pop()
    existingProjects = list(filter(lambda project: project.get('id') == projectName, session.get('{url}/api/Project'.format(url = environmentConfig.get('tilemillUrl'))).json()))
    if len(existingProjects) > 0:
        logging.info('Project {projectName} already in use, will be replaced'.format(projectName = projectName))
    centre = ogr.CreateGeometryFromWkt('POLYGON (({minX} {minY}, {maxX} {minY}, {maxX} {maxY}, {minX} {maxY}, {minX} {minY}))'.format(
        minX = bounds.get('minX'),
        minY = bounds.get('minY'),
        maxX = bounds.get('maxX'),
        maxY = bounds.get('maxY')
    )).Centroid().GetPoint()
    zoomLevels = list()
    scalesAndZooms = sourceConfig.get('tile').get('scales')
    scales = scalesAndZooms.keys()
    for scale in scales:
        for zoom in scalesAndZooms[scale]:
            zoomLevels.append(zoom)
    zoomLevels.sort()
    lowestZoom = zoomLevels[0]
    highestZoom = zoomLevels[len(zoomLevels) - 1]
    stylesheetEntries = ['Map { background-color: #fff }']
    for scale in scales:
        for zoomLevel in scalesAndZooms[scale]:
            stylesheetEntries.append('.{scale} [zoom = {zoom}] {{ raster-opacity: 1; }}'.format(scale = scale, zoom = zoomLevel))
    layers = list()
    srcCrs = CRS(sourceConfig.get('crs'))
    for scale in scales:
        for fileLocations in _getLayerFilePaths(projectDirectoryPath, scale, environmentConfig):
            srcLocation = fileLocations.get('tilemillLocation', fileLocations['srcLocation'])
            fileIdentifier = '{scale}_{filename}'.format(scale = str(scale), filename = re.sub(r'\.tif(f)?$', '', fileLocations.get('filename')))
            layers.append({
                'geometry': 'raster',
                'extent': _getExtentFromRaster(sourceConfig, fileLocations.get('srcLocation')),
                'id': fileIdentifier,
                'class': str(scale),
                'Datasource': { 'file': srcLocation },
                'layer': None,
                'srs-name': srcCrs.srs,
                'srs': srcCrs.to_proj4(),
                'advanced': {},
                'name': fileIdentifier
            })
    return {
        'minX': bounds.get('minX'),
        'minY': bounds.get('minY'),
        'maxX': bounds.get('maxX'),
        'maxY': bounds.get('maxY'),
        'centreX': centre[0],
        'centreY': centre[1],
        'lowestZoom': lowestZoom,
        'highestZoom': highestZoom,
        'styles': stylesheetEntries,
        'layers': layers,
        'projectName': projectName
    }


def _getExtentFromRaster(sourceConfig, path):
    image = gdal.Open(path)
    ulx, xres, xskew, uly, yskew, yres = image.GetGeoTransform()
    lrx = ulx + (image.RasterXSize * xres)
    lry = uly + (image.RasterYSize * yres)
    destCrs = CRS('EPSG:4326')
    srcCrs = CRS(sourceConfig.get('crs'))
    transformer = Transformer.from_crs(srcCrs, destCrs, always_xy = True)
    lowerRight = transformer.transform(lrx, lry)
    upperLeft = transformer.transform(ulx, uly)
    return {
        'minX': upperLeft[0],
        'minY': lowerRight[1],
        'maxX': lowerRight[0],
        'maxY': upperLeft[1]
    }


def _getLayerFilePaths(parentDirectory, scale, environmentConfig):
    layerFiles = list()
    srcDirectory = os.path.join(parentDirectory, str(scale))
    for filename in os.listdir(srcDirectory):
        if re.search(r'\.tif(f)?$', filename, re.IGNORECASE):
            layerFiles.append({ 'srcLocation': os.path.join(srcDirectory, filename), 'filename': filename })
    containerConfig = environmentConfig.get('container')
    if containerConfig != None:
        try:
            import docker
            alternateLayerFiles = list()
            client = docker.from_env()
            containerName = containerConfig.get('name')
            container = client.containers.get(containerName)
            containerBaseDir = containerConfig.get('dataDir')
            containerFileDir = containerBaseDir + ('' if containerBaseDir.endswith('/') else '/') + parentDirectory.split(os.path.sep).pop() + '/' + str(scale) + '/' # explicitly use unix path separators as container is Ubuntu
            container.exec_run('rm -rf ' + containerFileDir, stderr = True, stdout = True)
            container.exec_run('mkdir -p ' + containerFileDir, stderr = True, stdout = True)
            for layerFile in layerFiles:
                containerFile = containerFileDir + layerFile.get('filename')
                subprocess.check_output('docker cp ' + layerFile.get('srcLocation') + ' ' + containerName + ':' + containerFile, shell = True)
                alternateLayerFile = layerFile.copy()
                alternateLayerFile['tilemillLocation'] = containerFile
                alternateLayerFiles.append(alternateLayerFile)
            return alternateLayerFiles
        except ImportError:
            print ('no docker import available, dev config not possible')
    return layerFiles
                
