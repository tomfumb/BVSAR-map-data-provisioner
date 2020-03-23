import os
import math
import pyproj
import requests
import concurrent

from osgeo import gdal

from provisioners.Provisioner import Provisioner
from provisioners.ImageDimensions import ImageDimensions

class CanvecEn(Provisioner):

    crsEpsgCode = 'EPSG:3857'
    destCrs = None
    dpi = 96

    # ** should be determined from WMS GetCapabilities, not hard-coded
    maxW = 4096
    maxH = 4096

    maxAsyncRequests = 4

    scales = (250000, 150000, 70000, 35000)

    def __init__(self):
        self.destCrs = pyproj.Proj('+init={self.crsEpsgCode}'.format(self = self))

    def provision(self, minX, minY, maxX, maxY, outputDirectory):
        lowerLeft = pyproj.transform(self.srcCrs, self.destCrs, minX, minY)
        upperRight = pyproj.transform(self.srcCrs, self.destCrs, maxX, maxY)
        startPoint = list(map(lambda ord: math.floor(ord), lowerLeft))
        endPoint = list(map(lambda ord: math.ceil(ord), upperRight))
        totalWidthMetres = endPoint[0] - startPoint[0]
        totalHeightMetres = endPoint[1] - startPoint[1]
        imageRequests = dict()
        for scale in self.scales:
            imageRequests[scale] = list()
            remainingWidthMetres = totalWidthMetres
            remainingHeightMetres = totalHeightMetres
            nextImageData = self.getGridAxisAdvanceData(remainingHeightMetres, scale, self.maxH)
            nextImageHeightPixels, nextImageHeightMetres = nextImageData.nextImagePixels, nextImageData.nextImageMapUnits
            lastStartPoint = startPoint.copy()
            # advance along X axis from lower-left. Calculate all column dimensions for a single row
            while remainingWidthMetres > 0:
                nextImageData = self.getGridAxisAdvanceData(remainingWidthMetres, scale, self.maxW)
                nextImageWidthPixels, nextImageWidthMetres, remainingWidthMetres = nextImageData.nextImagePixels, nextImageData.nextImageMapUnits, remainingWidthMetres - nextImageData.remainingMapUnitReduction
                minX, minY = lastStartPoint[0], lastStartPoint[1]
                maxX, maxY = minX + nextImageWidthMetres, minY + nextImageHeightMetres
                imageRequests[scale].append([ImageDimensions(minX, minY, maxX, maxY, nextImageWidthPixels, nextImageHeightPixels)])
                lastStartPoint = (maxX, minY)
            remainingHeightMetres = remainingHeightMetres - (imageRequests[scale][0][0].maxY - imageRequests[scale][0][0].minY)
            # advance along Y axis from lower-left. Calculate all row dimensions for a single column
            while remainingHeightMetres > 0:
                baseImageRequest = imageRequests[scale][0][0]
                nextImageData = self.getGridAxisAdvanceData(remainingHeightMetres, scale, self.maxH)
                nextImageHeightPixels, nextImageHeightMetres, remainingHeightMetres = nextImageData.nextImagePixels, nextImageData.nextImageMapUnits, remainingHeightMetres - nextImageData.remainingMapUnitReduction
                minX, minY = baseImageRequest.minX, baseImageRequest.maxY
                maxX, maxY = baseImageRequest.maxX, baseImageRequest.maxY + nextImageHeightMetres
                imageRequests[scale][0].append(ImageDimensions(minX, minY, maxX, maxY, baseImageRequest.pixelX, nextImageHeightPixels))
            # fill gaps using single row and column to make a complete grid
            i = 1
            while i < len(imageRequests[scale]):
                j = 1
                while j < len(imageRequests[scale][0]):
                    xReference = imageRequests[scale][i][0]
                    yReference = imageRequests[scale][0][j]
                    imageRequests[scale][i].append(ImageDimensions(xReference.minX, yReference.minY, xReference.maxX, yReference.maxY, xReference.pixelX, yReference.pixelY))
                    j = j + 1
                i = i + 1

        # at this point we have determined all file requests that are required to cover the area, should be passed off to a separate component to issue the requests
        # one component executes requests and saves png files if not already existing
        # separate component converts to .tiff if not already existing
        # separate component merges files into big tiff? will have to check effects of merge on text quality
        
        fileRequests = list()
        for scale in imageRequests:
            i = 0
            for column in imageRequests[scale]:
                j = 0
                for cell in column:
                    url = \
                        'https://maps.geogratis.gc.ca/wms/canvec_en?' + \
                        'SERVICE=WMS&' + \
                        'VERSION=1.3.0&' + \
                        'REQUEST=GetMap&' + \
                        'BBOX={cell.minX},{cell.minY},{cell.maxX},{cell.maxY}&'.format(cell = cell) + \
                        'CRS={self.crsEpsgCode}&'.format(self = self) + \
                        'WIDTH={cell.pixelX}&HEIGHT={cell.pixelY}&'.format(cell = cell) + \
                        'LAYERS=canvec&' + \
                        'STYLES=&' + \
                        'FORMAT=image/png&' + \
                        'DPI={self.dpi}&MAP_RESOLUTION={self.dpi}&FORMAT_OPTIONS=dpi:{self.dpi}&'.format(self = self) + \
                        'TRANSPARENT=FALSE'
                    fileRequests.append(( \
                        os.path.join( \
                            outputDirectory, \
                            str(scale), \
                            'col{i}_row{j}.png'.format(i = i, j = j) \
                        ), \
                        url, \
                        cell \
                    ))
                    j = j + 1
                i = i + 1

        # ensure directories exist before async execution begins to avoid race condition
        for fileRequest in fileRequests:
            os.makedirs(os.path.dirname(fileRequest[0]), exist_ok = True)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers = self.maxAsyncRequests) as executor:
            requestFutures = (executor.submit(self.issueFileRequest, fileRequest) for fileRequest in fileRequests)
            for future in concurrent.futures.as_completed(requestFutures):
                try:
                    future.result()
                except Exception as exc:
                    print ('exception: ' + str(type(exc)))

    def getGridAxisAdvanceData(self, remainingMapUnits, scale, maxPixels):
        remainingPixels = self.mapUnitsToPixels(remainingMapUnits, scale)
        if remainingPixels < maxPixels:
            return GridAxisAdvanceData(remainingPixels, remainingMapUnits, remainingMapUnits)
        else:
            maxPixelsInMapUnits = self.pixelsToMapUnits(maxPixels, scale)
            return GridAxisAdvanceData(maxPixels, maxPixelsInMapUnits, maxPixelsInMapUnits)

    def issueFileRequest(self, fileRequest):
        filePath = fileRequest[0]
        if os.path.exists(filePath) and os.stat(filePath).st_size > 0:
            print ('skipping ' + filePath)
        else:
            print ('requesting ' + filePath)
            url = fileRequest[1]
            imageRequest = fileRequest[2]
            out = open(filePath, 'wb')
            out.write(requests.get(url).content)
            out.close()
            png = gdal.Open(filePath, gdal.GA_ReadOnly)
            gdal.Translate( \
                '.'.join((filePath, 'tiff')), \
                png, \
                format = 'GTiff', \
                noData = 0, \
                outputSRS = self.crsEpsgCode, \
                # Translate expects bounds in format ulX, ulY, lrX, lrY so flip minY and maxY
                outputBounds = (imageRequest.minX, imageRequest.maxY, imageRequest.maxX, imageRequest.minY) \
            )

    def mapUnitsToPixels(self, mapUnits, scale):
        return (mapUnits / scale) / self.mapUnitsPerInch * self.dpi

    def pixelsToMapUnits(self, pixels, scale):
        return ((pixels * scale) / self.dpi) * self.mapUnitsPerInch



class GridAxisAdvanceData:

    def __init__(self, nextImagePixels, nextImageMapUnits, remainingMapUnitReduction):
        self.nextImagePixels, self.nextImageMapUnits, self.remainingMapUnitReduction = nextImagePixels, nextImageMapUnits, remainingMapUnitReduction