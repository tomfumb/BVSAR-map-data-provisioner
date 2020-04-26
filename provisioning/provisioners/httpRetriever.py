import re
import os
import random
import requests
import logging

from concurrent import futures

from osgeo import gdal

def httpRetriever(requests):
    with futures.ThreadPoolExecutor(max_workers = 1) as executor:
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
        response = requests.get(url, headers = { 'User-Agent': getRandomUserAgent() })
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

# https://www.scrapehero.com/how-to-fake-and-rotate-user-agents-using-python-3/
def getRandomUserAgent():
    userAgentList = (
        #Chrome
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        #Firefox
        'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
    )
    return random.choice(userAgentList)