import re
import os
import requests
import logging

from concurrent import futures

from osgeo import gdal

def httpRetriever(requests):
    with futures.ThreadPoolExecutor(max_workers = 4) as executor:
        requestFutures = (executor.submit(issueFileRequest, request) for request in requests)
        for future in futures.as_completed(requestFutures):
            try:
                future.result()
            except Exception as exc:
                logging.info('Exception: %s', str(type(exc)))


def issueFileRequest(request):
    filePath = request.get('path')
    if os.path.exists(filePath) and os.stat(filePath).st_size > 0:
        logging.debug('Skipping %s as it already exists', filePath)
    else:
        os.makedirs(os.path.dirname(filePath), exist_ok = True)
        url = request.get('url')
        logging.debug('Requesting %s from %s', filePath, url)
        response = requests.get(url)
        isExpectedType = isExpectedResponseType(response, request.get('expectedType'))
        if isExpectedType is None:
            logging.info('Cannot determine response type, may not be the desired response')
        else:
            if isExpectedType:
                logging.debug('Response is of expected type')
                out = open(filePath, 'wb') 
                out.write(response.content)
                out.close()
            else:
                logging.error('Response is not of expected type "%s", result will not be stored', request.get('expectedType'))
   

def isExpectedResponseType(response, expectedType):
    responseType = response.headers.get('Content-Type')
    if responseType != None:
        if re.match(re.escape(expectedType), responseType) != None:
            return True
        else:
            return False
    else:
        return None