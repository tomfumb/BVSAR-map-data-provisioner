import os
import re
import random
import datetime
import pytz
import requests
import ogr
import gdal
import json
import logging
import pyproj
import subprocess
import time
import sys

class TileMillManager:

    # need to accommodate that this is just one way of providing data - should make specific to tiff data so that e.g. shapefile can do the same

    def __init__(self):
        try:
            import http.client as http_client
        except ImportError:
            # Python 2
            import httplib as http_client
        http_client.HTTPConnection.debuglevel = 1
        # You must initialize logging, otherwise you'll not see debug output.
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    def generate(self, parentDirectory, scalesAndZooms, minX, minY, maxX, maxY, environmentConfig): 

        ### need a deterministic way to get projectName - keep creating new projects when not necessary. Perhaps last modified date of a file?

        projectName = 'auto_{nowTs}'.format(nowTs = self._getNowAsEpochMs())
        session = requests.session()
        existingProjects = session.get(environmentConfig['tilemillUrl'] + 'api/Project').json()
        projectNameTaken = False
        for existingProject in existingProjects:
            if (existingProject["id"] == projectName):
                projectNameTaken = True
                break
        if (projectNameTaken):
            print ('project {projectName} already in use, not doing anything'.format(projectName = projectName))
            # return
        centre = ogr.CreateGeometryFromWkt('POLYGON (({minX} {minY}, {maxX} {minY}, {maxX} {maxY}, {minX} {maxY}, {minX} {minY}))'.format(minX = minX, minY = minY, maxX = maxX, maxY = maxY)).Centroid().GetPoint()

        scales = scalesAndZooms.keys()
        zoomLevels = list()
        for scale in scales:
            for zoom in scalesAndZooms[scale]:
                zoomLevels.append(zoom)
        zoomLevels.sort()
        lowestZoom = zoomLevels[0]
        highestZoom = zoomLevels[len(zoomLevels) - 1]

        stylesheetEntries = ['Map { background-color: #fff }']
        for scale in scales:
            for zoomLevel in scalesAndZooms[scale]:
                stylesheetEntries.append('.{scale} [zoom = {zoom}] {{ raster-opacity: 1; }}'.format(scale = str(scale), zoom = zoomLevel))

        layers = list()
        for scale in scales:
            for fileLocations in self._getLayerFilePaths(parentDirectory, scale, environmentConfig):
                srcLocation = fileLocations.get('tilemillLocation', fileLocations['srcLocation'])
                fileIdentifier = '{scale}_{filename}'.format(scale = str(scale), filename = re.sub(r'\.tiff$', '', fileLocations['filename']))
                layers.append({ \
                    'geometry': 'raster', \
                    'extent': self._getExtentFromRaster(fileLocations['srcLocation']), \
                    'id': fileIdentifier, \
                    'class': str(scale), \
                    'Datasource': { 'file': srcLocation }, \
                    'layer': None, \
                    'srs-name': '900913', \
                    'srs': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over', \
                    'advanced': {}, \
                    'name': fileIdentifier
                })

        token = self._generateToken()
        projectDefinition = { \
            'bounds': (minX, minY, maxX, maxY), \
            'center': (centre[0], centre[1], lowestZoom), \
            'format': 'png8', \
            'interactivity': False, \
            'minzoom': lowestZoom, \
            'maxzoom': highestZoom, \
            'srs': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over', \
            'Stylesheet': list(map(lambda entry: {'data': entry[1], 'id': str(entry[0]) + '.mss'}, enumerate(stylesheetEntries))), \
            'Layer': layers, \
            'scale': 1, \
            'metatile': 2, \
            'id': projectName, \
            'name': '', \
            'description': '', \
            'use-default': False, \
            'bones.token': token \
        }
        session.put( \
            environmentConfig['tilemillUrl'] + 'api/Project/' + projectName, \
            data = json.dumps(projectDefinition), \
            headers = { 'Content-Type': 'application/json' }, \
            cookies = { 'bones.token': token } \
        )

        token = self._generateToken()
        nowTs = self._getNowAsEpochMs()
        exportDefinition = { \
            'progress': 0, \
            'status': 'waiting', \
            'format': 'mbtiles', \
            'project': projectName, \
            'id': projectName, \
            'zooms': (lowestZoom, highestZoom), \
            'metatile': 2, \
            'center': (centre[0], centre[1], lowestZoom), \
            'bounds': (minX, minY, maxX, maxY), \
            'static_zoom': lowestZoom, \
            'filename': '{projectName}.mbtiles'.format(projectName = projectName), \
            'note': '', \
            'bbox': (minX, minY, maxX, maxY), \
            'minzoom': lowestZoom, \
            'maxzoom': highestZoom, \
            'bones.token': token
        }
        session.put( \
            environmentConfig['tilemillUrl'] + 'api/Export/' + str(nowTs), \
            data = json.dumps(exportDefinition), \
            headers = { 'Content-Type': 'application/json' }, \
            cookies = { 'bones.token': token } \
        )

        isComplete = False
        while isComplete == False:
            try:
                statuses = session.get(environmentConfig['tilemillUrl'] + 'api/Export').json()
                remaining = None
                for status in statuses:
                    statusProject = status.get('project', None)
                    if statusProject == projectName:
                        remaining = status.get('remaining', sys.maxsize)
                        print ('project {projectName} remaining: {remaining}ms'.format(projectName = projectName, remaining = str(remaining)))
                        if remaining == 0:
                            isComplete = True
                        else:
                            time.sleep(min(5, remaining / 1000))
                if remaining == None:
                    print ('no status available for current project, something went wrong')
                    break
            except:
                print ('api rejected request for update')
                break
        print ('export complete')

        response = requests.get('{baseUrl}export/download/{projectName}.mbtiles'.format(baseUrl = environmentConfig['tilemillUrl'], projectName = projectName))
        with open(os.path.join(parentDirectory, 'output.mbtiles'), 'wb') as file:
            file.write(response.content)
        print ('finished')

    def _generateToken(self):
        characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXZY0123456789'
        token = ''
        while len(token) < 32:
            token = token + characters[random.randint(0, len(characters) - 1)]
        return token

    def _generateTokenCookie(self, token, projectName): 
        expiryTime = datetime.datetime.now(tz = pytz.UTC) + datetime.timedelta(seconds = 2)
        return 'bones.token={token};expires={expiry};path=/api/Project/{projectName}'.format( \
            token = token, \
            expiry = expiryTime.strftime('%a, %d %b %Y %H:%M:%S %Z'), \
            projectName = projectName \
        )

    def _getNowAsEpochMs(self):
        return int(datetime.datetime.now().timestamp())

    # def _getProjectNameFromDirectory(self, directory): 
    #     pathParts = directory.split(os.path.sep)
    #     lastPart = pathParts[len(pathParts) - 1]
    #     return re.sub(r"[^a-zA-Z0-9\-]", "_", lastPart)

    def _getExtentFromRaster(self, path):
        image = gdal.Open(path)
        ulx, xres, xskew, uly, yskew, yres = image.GetGeoTransform()
        lrx = ulx + (image.RasterXSize * xres)
        lry = uly + (image.RasterYSize * yres)
        srcCrs = pyproj.Proj('+init=EPSG:3857')
        destCrs = pyproj.Proj('+init=EPSG:4326')
        lowerRight = pyproj.transform(srcCrs, destCrs, lrx, lry)
        upperLeft = pyproj.transform(srcCrs, destCrs, ulx, uly)
        return (upperLeft[0], lowerRight[1], lowerRight[0], upperLeft[1])

    def _getLayerFilePaths(self, parentDirectory, scale, environmentConfig):
        layerFiles = list()
        srcDirectory = os.path.join(parentDirectory, str(scale))
        for filename in os.listdir(srcDirectory):
            if filename.endswith('.tiff'):
                layerFiles.append({'srcLocation': os.path.join(srcDirectory, filename), 'filename': filename})

        if (environmentConfig['container'] != None):
            try:
                import docker
                alternateLayerFiles = list()
                client = docker.from_env()
                containerName = environmentConfig['container']['name']
                container = client.containers.get(containerName)
                containerBaseDir = environmentConfig['container']['dataDir']
                containerFileDir = containerBaseDir + ('' if containerBaseDir.endswith('/') else '/') + str(scale) + '/' # explicitly use unix path separators as container is Ubuntu
                container.exec_run('rm -rf ' + containerFileDir, stderr = True, stdout = True)
                container.exec_run('mkdir -p ' + containerFileDir, stderr = True, stdout = True)
                for layerFile in layerFiles:
                    containerFile = containerFileDir + layerFile['filename']
                    subprocess.check_output('docker cp ' + layerFile['srcLocation'] + ' ' + containerName + ':' + containerFile, shell = True)
                    alternateLayerFile = layerFile.copy()
                    alternateLayerFile['tilemillLocation'] = containerFile
                    alternateLayerFiles.append(alternateLayerFile)
                return alternateLayerFiles

            except ImportError:
                print ('no docker import available, dev config not possible')
        
        return layerFiles
                

