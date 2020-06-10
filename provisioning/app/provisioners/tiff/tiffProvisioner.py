import os
from osgeo import ogr, gdal
import glob
import logging

from shutil import copyfile

from provisioners.tilemill.tiffProjectManager import generateTilesFromTiff

from provisioners.validators.globPathContentValidator import globPathContentValidator

def provision(sourceConfig, stringUserArgs, environmentConfig, projectDirectoryPath):
    globPath = sourceConfig.get('pathPattern')
    globPathContentValidator(globPath)
    sourceFilePaths = glob.glob(globPath)
    bounds = getBoundsForImages(sourceFilePaths)
    stageFiles(sourceConfig, sourceFilePaths, projectDirectoryPath)
    generateTilesFromTiff(sourceConfig, bounds, projectDirectoryPath, environmentConfig)


def getBoundsForImages(sourceFilePaths):
    extent = ogr.Geometry(ogr.wkbMultiPolygon)
    for sourceFilePath in sourceFilePaths:
        image = gdal.Open(sourceFilePath)
        ulx, xres, xskew, uly, yskew, yres = image.GetGeoTransform()
        lrx = ulx + (image.RasterXSize * xres)
        lry = uly + (image.RasterYSize * yres)
        imageExtent = ogr.CreateGeometryFromWkt('POLYGON (({minX} {minY}, {maxX} {minY}, {maxX} {maxY}, {minX} {maxY}, {minX} {minY}))'.format(
            minX = ulx,
            minY = lry,
            maxX = lrx,
            maxY = uly
        ))
        extent.AddGeometry(imageExtent)
    envelope = extent.GetEnvelope()
    return {
        'minX': envelope[0],
        'minY': envelope[2],
        'maxX': envelope[1],
        'maxY': envelope[3]
    }


def stageFiles(sourceConfig, sourceFilePaths, projectDirectoryPath):
    scalesAndZooms = sourceConfig.get('tile').get('scales')
    scales = list(scalesAndZooms.keys())
    if len(scales) != 1 or scales[0] != 'all':
        logging.warn('tiff provisioning source configuration is incorrect. Provide zooms for the "all" scale only')
        raise ValueError('scales configured incorrectly')
    destinationDirectoryPath = os.path.join(projectDirectoryPath, 'all')
    os.makedirs(destinationDirectoryPath, exist_ok = True)
    for sourceFilePath in sourceFilePaths:
        destinationFilePath = os.path.join(destinationDirectoryPath, sourceFilePath.split(os.path.sep).pop())
        copyfile(sourceFilePath, destinationFilePath)