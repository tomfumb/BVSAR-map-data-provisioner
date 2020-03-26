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

class TileMillManager:

    # need to accommodate that this is just one way of providing data - should make specific to tiff data so that e.g. shapefile can do the same

    url = 'http://localhost:20009/'

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

    def generate(self, parentDirectory, scalesAndZooms, minX, minY, maxX, maxY): 
        projectName = self._getProjectNameFromDirectory(parentDirectory)
        session = requests.session()
        existingProjects = session.get(self.url + 'api/Project').json()
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

        layers = list()
        for scale in scales:
            for filename in os.listdir(os.path.join(parentDirectory, str(scale))):
                if filename.endswith('.tiff'):

                    ## CURRENT issue - files are not available in docker volume, need copying to it before can reference in tilemill project
                    ## will not be an issue when run in Docker container, dev issue only so solution does not need to be perfect

                    try:
                        import docker
                        client = docker.from_env()
                        container = client.containers.get("tilemill")
                        container.put_archive()
                    except ImportError:
                        print ('no docker import available')




                    layers.append({ \
                        'geometry': 'raster', \
                        'extent': self._getExtentFromRaster(os.path.join(parentDirectory, str(scale), filename)), \
                        'id': re.sub(r'\.tiff$', '', filename), \
                        'class': scale, \
                        'Datasource': { 'file': os.path.join(parentDirectory, str(scale), filename) }, \
                        'layer': None, \
                        'srs-name': '900913', \
                        'srs': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over', \
                        'advanced': {}, \
                        'name': re.sub(r'\.tiff$', '', filename)
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
            'Stylesheet': (), \
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
            self.url + 'api/Project/' + projectName, \
            data = json.dumps(projectDefinition), \
            headers = { 'Content-Type': 'application/json' }, \
            cookies = { 'bones.token': token } \
        )



        # PUT to http://localhost:20009/api/Project/-127_657_54_6035_-126_579_54_9548_canvec_en (replae all commas & periods with underscores)
        # Payload: {"bounds":[-180,-85.05112877980659,180,85.05112877980659],"center":[0,0,2],"format":"png8","interactivity":false,"minzoom":0,"maxzoom":22,"srs":"+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over","Stylesheet":[{"data":"Map {\n  background-color: #b8dee6;\n}\n\n","id":"style.mss"}],"Layer":[],"scale":1,"metatile":2,"id":"-127_657_54_6035_-126_579_54_9548_canvec_en","name":"","description":"","use-default":false,"bones.token":"PcNzNpHzFaB8TKIIWos902OfhPfWPbEv"}
        # Token generated with following JavaScript
# Backbone.csrf = function(path, timeout) {
#     var chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXZY0123456789';
#     var token = '';
#     while (token.length < 32) {
#         token += chars.charAt(Math.floor(Math.random() * chars.length));
#     }

#     // Remove hashes, query strings from cookie path.
#     path = path || '/';
#     path = path.split('#')[0].split('?')[0];

#     var expires = new Date(+new Date + (timeout || 2000)).toGMTString();
#     document.cookie = 'bones.token=' + token
#         + ';expires=' + expires
#         + ';path=' + path + ';';
#     return token;
# };
        # first have to query projects with GET http://localhost:20009/api/Project, "name" property important
        # Add Layer in the UI doesn't change anything, clicking "Save" PUTs the entire project like this:
# {"bounds":[-180,-85.05112877980659,180,85.05112877980659],"center":[0,0,2],"format":"png8","interactivity":false,"minzoom":0,"maxzoom":22,"srs":"+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over","Stylesheet":[{"data":"Map {\n  background-color: #b8dee6;\n}\n\n.35000 { raster-opacity: 1; }","id":"style.mss"}],"Layer":[{"geometry":"raster","extent":[-127.65700686135976,54.60349625574196,-127.31626988532467,54.80038381567145],"id":"col0row0","class":"35000","Datasource":{"file":"/root/Documents/tile/input/col0_row0.png.tiff"},"layer":null,"srs-name":"900913","srs":"+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over","advanced":{},"name":"col0row0"},{"geometry":"raster","extent":[-127.65700686135976,54.80038381567145,-127.31626988532467,54.95480179615438],"id":"col0row1","class":"35000","Datasource":{"file":"/root/Documents/tile/input/col0_row1.png.tiff"},"layer":null,"srs-name":"900913","srs":"+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over","advanced":{},"name":"col0row1"}],"scale":1,"metatile":2,"id":"-127_657_54_6035_-126_579_54_9548_canvec_en","_updated":1585069205000,"name":"","description":"","tilejson":"2.0.0","scheme":"xyz","tiles":["http://0.0.0.0:20008/tile/-127_657_54_6035_-126_579_54_9548_canvec_en/{z}/{x}/{y}.png?updated=1585069205000&metatile=2&scale=1"],"grids":["http://0.0.0.0:20008/tile/-127_657_54_6035_-126_579_54_9548_canvec_en/{z}/{x}/{y}.grid.json?updated=1585069205000&metatile=2&scale=1"],"template":"","lastBrowsedFolder":"/root/Documents/tile/input","bones.token":"z0yy2brjLBfQQDFYgqumAAKTWzwmrAlU"}
        # So I should actually be able to create the project in one shot with all layers and styles

        # export request is a PUT to http://localhost:20009/api/Export/1585069712593
        # PUT payload: {"progress":0,"status":"waiting","format":"mbtiles","project":"-127_657_54_6035_-126_579_54_9548_canvec_en","id":"1585069712593","zooms":[12,16],"metatile":2,"center":[-127.4785,54.7833,10],"bounds":[-180,-85.05112877980659,180,85.05112877980659],"static_zoom":2,"tiles":["http://0.0.0.0:20008/tile/-127_657_54_6035_-126_579_54_9548_canvec_en/{z}/{x}/{y}.png?updated=1585069600000&metatile=2&scale=1"],"filename":"-127_657_54_6035_-126_579_54_9548_canvec_en.mbtiles","note":"","bbox":[-127.6529,54.6087,-127.3192,54.9508],"minzoom":12,"maxzoom":16,"bones.token":"5BevHDNLaP3i2wC0lbPgjBupktyEAuF7"}
        # this one failed, perhaps due to special characters in filename?

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

    def _getProjectNameFromDirectory(self, directory): 
        pathParts = directory.split(os.path.sep)
        lastPart = pathParts[len(pathParts) - 1]
        return re.sub(r"[^a-zA-Z0-9\-]", "_", lastPart)

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