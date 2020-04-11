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
        out = open(filePath, 'wb')
        out.write(requests.get(url).content)
        out.close()
   