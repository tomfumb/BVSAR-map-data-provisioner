import glob
import logging

def globPathContentValidator(globPath):
    sourceFilePaths = glob.glob(globPath)
    if len(sourceFilePaths) == 0:
        logging.warn('No files available at %s', globPath)
        raise ValueError('No files available at %s', globPath)