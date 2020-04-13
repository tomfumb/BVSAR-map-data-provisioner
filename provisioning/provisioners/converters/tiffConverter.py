import os
import re
import gdal
import logging

def tiffConverter(filesToConvert, srsCode):
    for fileToConvert in filesToConvert:
        sourcePath = fileToConvert.get('path')
        destinationPath = re.sub(r'\.[a-zA-Z0-9]+$', '.tiff', sourcePath)
        if os.path.exists(sourcePath):
            if os.path.exists(destinationPath) and os.stat(destinationPath).st_size > 0:
                logging.debug('Skipping %s as it already exists', destinationPath)
            else:
                logging.debug('Converting %s to %s', sourcePath, destinationPath)
                bbox = fileToConvert.get('bbox')
                sourceFile = gdal.Open(sourcePath, gdal.GA_ReadOnly)
                gdal.Translate(
                    destinationPath,
                    sourceFile,
                    format = 'GTiff',
                    noData = 0,
                    outputSRS = srsCode,
                    # Translate expects bounds in format ulX, ulY, lrX, lrY so flip minY and maxY
                    outputBounds = (bbox.get('minX'), bbox.get('maxY'), bbox.get('maxX'), bbox.get('minY'))
                )
        else:
            logging.warn('Expected file %s does not exist', sourcePath)
