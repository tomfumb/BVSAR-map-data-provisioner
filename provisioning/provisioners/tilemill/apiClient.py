import os
import json
import random
import logging
import datetime
import requests

def createOrUpdateProject(projectDefinition, environmentConfig):
    token = _generateToken()
    projectDefinition = { \
        'bounds': (projectDefinition.get('minX'), projectDefinition.get('minY'), projectDefinition.get('maxX'), projectDefinition.get('maxY')), \
        'center': (projectDefinition.get('centreX'), projectDefinition.get('centreY'), projectDefinition.get('lowestZoom')), \
        'format': 'png8', \
        'interactivity': False, \
        'minzoom': projectDefinition.get('lowestZoom'), \
        'maxzoom': projectDefinition.get('highestZoom'), \
        'srs': '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0.0 +k=1.0 +units=m +nadgrids=@null +wktext +no_defs +over', \
        'Stylesheet': list(map(lambda entry: {'data': entry[1], 'id': str(entry[0]) + '.mss'}, enumerate(projectDefinition.get('styles')))), \
        'Layer': projectDefinition.get('layers'), \
        'scale': 1, \
        'metatile': 2, \
        'id': projectDefinition.get('projectName'), \
        'name': '', \
        'description': '', \
        'use-default': False, \
        'bones.token': token \
    }
    requests.put( \
        '{url}/api/Project/{projectName}'.format(url = environmentConfig.get('tilemillUrl'), projectName = projectDefinition.get('projectName')),
        data = json.dumps(projectDefinition),
        headers = { 'Content-Type': 'application/json' },
        cookies = { 'bones.token': token }
    )


def requestExport(userArgs, projectDefinition, projectDirectoryPath, environmentConfig):
    token = _generateToken()
    nowTs = _getNowAsEpochMs()
    projectName = projectDefinition.get('projectName')
    lowestZoom = projectDefinition.get('lowestZoom')
    highestZoom = projectDefinition.get('highestZoom')
    minX, minY, maxX, maxY = userArgs.get('minX'), userArgs.get('minY'), userArgs.get('maxX'), userArgs.get('maxY')
    centreX, centreY = userArgs.get('centreX'), userArgs.get('centreY')
    exportDefinition = {
        'progress': 0,
        'status': 'waiting',
        'format': 'mbtiles',
        'project': projectName,
        'id': projectName,
        'zooms': (lowestZoom, highestZoom),
        'metatile': 2,
        'center': (centreX, centreY, lowestZoom),
        'bounds': (minX, minY, maxX, maxY),
        'static_zoom': lowestZoom,
        'filename': '{projectName}.mbtiles'.format(projectName = projectName),
        'note': '',
        'bbox': (minX, minY, maxX, maxY),
        'minzoom': lowestZoom,
        'maxzoom': highestZoom,
        'bones.token': token
    }
    requests.put(
        '{url}/api/Export/{nowTs}'.format(url = environmentConfig.get('tilemillUrl'), nowTs = nowTs),
        data = json.dumps(exportDefinition),
        headers = { 'Content-Type': 'application/json' },
        cookies = { 'bones.token': token }
    )
    isComplete = False
    while isComplete == False:
        try:
            statuses = requests.get('{url}/api/Export'.format(url = environmentConfig.get('tilemillUrl'))).json()
            remaining = None
            for status in statuses:
                statusProject = status.get('project', None)
                if statusProject == projectName:
                    remaining = status.get('remaining', sys.maxsize)
                    logging.debug('Project %s remaining: %dms', projectName, remaining)
                    if remaining == 0:
                        isComplete = True
                    else:
                        time.sleep(min(5, remaining / 1000))
            if remaining == None:
                logging.warn('No status available for current project, something went wrong')
                break
        except:
            logging.warn('API rejected request for update')
            break
    logging.info('Export complete')

    response = requests.get('{url}/export/download/{projectName}.mbtiles'.format(url = environmentConfig.get('tilemillUrl'), projectName = projectName))
    with open(os.path.join(projectDirectoryPath, 'output.mbtiles'), 'wb') as file:
        file.write(response.content)
    logging.info('Finished')


def _generateToken():
    characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXZY0123456789'
    token = ''
    while len(token) < 32:
        token = token + characters[random.randint(0, len(characters) - 1)]
    return token


def _getNowAsEpochMs():
    return int(datetime.datetime.now().timestamp())