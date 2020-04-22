import argparse
import os
import yaml
import logging
import sys
import base64
import datetime

from provisioners.tiff.tiffProvisioner import provision as tiffProvisioner
from provisioners.wms.wmsTileProvisioner import provision as wmsTileProvisioner
from provisioners.namers.sourceAndArgNamer import sourceAndArgNamer

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('src', type = str, help = 'Data source name')
    parser.add_argument('--dev', default = False, const = True, dest='dev', action='store_const', help = 'Whether to execute in dev mode (Python executing outside Docker container)')
    parser.add_argument('--sourceArgs', default = '', type = str, help = 'Arguments specific to the type of the data source. Comma-separated, key=value format. E.g. sourceArgs=a=1,b=2,c=3)')
    args = vars(parser.parse_args())

    if args['dev']:
        environmentConfigFile = 'dev'
    else:
        environmentConfigFile = 'prod'
    configPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', '.'.join((environmentConfigFile, 'yaml')))
    with open(configPath, 'r') as configFile:
        environmentConfig = yaml.safe_load(configFile)

    sourceConfigFileName = getAbsolutePath(os.path.join('sources', '.'.join((args['src'], 'yaml'))))
    with open(sourceConfigFileName, 'r') as sourceConfigFile:
        sourceConfig = yaml.safe_load(sourceConfigFile)

    sourceArgs = {}
    for argPair in list(filter(lambda entry: entry if entry != '' else None, str(args.get('sourceArgs', '')).split(','))):
        argPairParts = argPair.split('=')
        sourceArgs[argPairParts[0]] = argPairParts[1]

    sourceTypes = {
        'wms': {
            'provisioner':  wmsTileProvisioner,
            'projectNamer': sourceAndArgNamer
        },
        'tiff': {
            'provisioner': tiffProvisioner,
            'projectNamer': sourceAndArgNamer
        }
    }

    sourceType = sourceTypes.get(sourceConfig['type'])
    projectName = sourceType.get('projectNamer')(args.get('src'), sourceArgs)
    projectDirectory = getAbsolutePath(os.path.join('output', projectName))
    os.makedirs(projectDirectory, exist_ok = True)
    configureLogger(environmentConfig, projectDirectory)
    logging.debug('Called with %s', str(sourceArgs))

    sourceType.get('provisioner')(sourceConfig, sourceArgs, environmentConfig, projectDirectory)
    

def getAbsolutePath(relativePath):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relativePath)


def configureLogger(environmentConfig, projectDirectory):
    logDirectory = os.path.join(projectDirectory, 'log')
    os.makedirs(logDirectory, exist_ok = True)
    requestedLogLevel = environmentConfig.get('logLevel', 'error')
    logLevelMapping = {
        'debug': logging.DEBUG,
        'info':  logging.INFO,
        'warn':  logging.WARN,
        'error': logging.ERROR
    }
    handlers = [
        logging.StreamHandler(stream = sys.stdout),
        logging.FileHandler(os.path.join(logDirectory, '{nowTs}.log'.format(nowTs = str(int(datetime.datetime.now().timestamp())))))
    ]
    logging.basicConfig(handlers = handlers, level = logLevelMapping.get(requestedLogLevel, logging.ERROR), format = '%(levelname)s %(asctime)s %(message)s')


if __name__ == '__main__':
    main()
