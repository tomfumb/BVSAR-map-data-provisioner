import math
import pyproj
from functools import reduce

from provisioners.Provisioner import Provisioner
from provisioners.ImageRequestProperties import ImageRequestProperties

class CanvecEn(Provisioner):

    destCrs = None
    dpi = 96
    maxW = 4096
    maxH = 4096
    scales = (250000, 150000, 70000, 35000)

    def __init__(self):
        self.destCrs = pyproj.Proj('+init=EPSG:3857')

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
            remainingHeightPixels = self.metresToPixels(remainingHeightMetres, scale)
            nextImageHeightPixels = min(remainingHeightPixels, self.maxH)
            nextImageHeightMetres = math.floor(self.pixelsToMetres(nextImageHeightPixels, scale))
            lastStartPoint = startPoint.copy()
            while remainingWidthMetres > 0:
                remainingWidthPixels = self.metresToPixels(remainingWidthMetres, scale)
                nextImageWidthPixels = min(remainingWidthPixels, self.maxW)
                nextImageWidthMetres = self.pixelsToMetres(nextImageWidthPixels, scale)
                remainingWidthMetres = remainingWidthMetres - nextImageWidthMetres
                minX, minY = lastStartPoint[0], lastStartPoint[1]
                maxX, maxY = minX + nextImageWidthMetres, minY + nextImageHeightMetres
                imageRequests[scale].append([ImageRequestProperties(minX, minY, maxX, maxY, nextImageWidthPixels, nextImageHeightPixels)])
                lastStartPoint = (maxX, minY)
            remainingHeightMetres = remainingHeightMetres - self.getTotalRequestedHeight(imageRequests[scale][0])
            while remainingHeightMetres > 0:
                baseImageRequest = imageRequests[scale][0][0]
                remainingHeightPixels = self.metresToPixels(remainingHeightMetres, scale)
                nextImageHeightPixels = min(remainingHeightPixels, self.maxH)
                nextImageHeightMetres = self.pixelsToMetres(nextImageHeightPixels, scale)
                minX, minY = baseImageRequest.minX, baseImageRequest.maxY
                maxX, maxY = baseImageRequest.maxX, baseImageRequest.maxY + nextImageHeightMetres
                imageRequests[scale][0].append(ImageRequestProperties(minX, minY, maxX, maxY, baseImageRequest.pixelX, nextImageHeightPixels))
                remainingHeightMetres = remainingHeightMetres - self.getTotalRequestedHeight(imageRequests[scale][0])
        print('got to here')

    def metresToPixels(self, metres, scale):
        return (metres / scale) / self.metresPerInch * self.dpi
        # return list(map(lambda inches: inches * self.dpi, map(lambda metres: (metres / scale) / self.metresPerInch, (x, y))))

    def pixelsToMetres(self, pixels, scale):
        return ((pixels * scale) / self.dpi) * self.metresPerInch
        # return list(map(lambda inches: inches * self.metresPerInch, map(lambda pixels: (pixels * scale) / self.dpi, (x, y))))

    def getTotalRequestedHeight(self, imageRequestList):
        return reduce(lambda total, next: total + next, map(lambda imageRequestProperties: imageRequestProperties.maxY - imageRequestProperties.minY, imageRequestList))
