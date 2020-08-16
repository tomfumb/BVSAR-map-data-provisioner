import re
import os
import sys
import random
import requests
import logging

from pydantic import BaseModel
from typing import List

from concurrent import futures
from timeit import default_timer as timer

class RetrievalRequest(BaseModel):
    path: str
    url: str
    expected_type: str

class ExistsCheckRequest(BaseModel):
    url: str

def check_exists(check_requests: List[ExistsCheckRequest]) -> None:
    for request in check_requests:
        if requests.head(request.url).status_code != 200:
            raise ValueError(f"{request.url} does not exist")


def httpRetriever(retrieval_requests: List[RetrievalRequest], maxConcurrentRequests: int = 10):
    requests = retrieval_requests.copy()
    if len(requests) > 0:
        bestTimePerRequest = sys.maxsize
        bestConcurrency = 1
        concurrency = 1
        while concurrency <= maxConcurrentRequests:
            logging.debug('Testing request speed with %d concurrent requests', concurrency)
            bestConcurrency = concurrency
            numRequestsToTest = min(concurrency, len(requests))
            logging.debug('Got %d requests to test with', numRequestsToTest)
            if numRequestsToTest > 0:
                testRequests = requests[:numRequestsToTest]
                del requests[:numRequestsToTest]
                start = timer()
                with futures.ThreadPoolExecutor(max_workers = numRequestsToTest) as executor:
                    executeRequests(executor, testRequests)
                end = timer()
                testTimePerRequest = (end - start) / numRequestsToTest
                logging.debug('Time per request %s', testTimePerRequest)
                if testTimePerRequest < bestTimePerRequest:
                    logging.debug('Got new best time')
                    bestTimePerRequest = testTimePerRequest
                else:
                    bestConcurrency = concurrency - 1
                    logging.debug('Previous time per request was better, exit and use %d', bestConcurrency)
                    break
                concurrency += 1
            else:
                break
        
        logging.info('Issuing requests with %d concurrency', bestConcurrency)
        with futures.ThreadPoolExecutor(max_workers = bestConcurrency) as executor:
            executeRequests(executor, requests)


def executeRequests(executor, requests: List[RetrievalRequest]) -> None:
    requestFutures = (executor.submit(issueFileRequest, request) for request in requests)
    for future in futures.as_completed(requestFutures):
        try:
            future.result()
        except Exception as exc:
            logging.info('Exception: %s', str(type(exc)))


def issueFileRequest(request: RetrievalRequest):
    filePath = request.path
    os.makedirs(os.path.dirname(filePath), exist_ok = True)
    url = request.url
    logging.info('Requesting %s from %s', filePath, url)
    response = requests.get(url, headers = { 'User-Agent': getRandomUserAgent() })
    isExpectedType = isExpectedResponseType(response, request.expected_type)
    if isExpectedType is None:
        logging.info('Cannot determine response type, may not be the desired response')
    else:
        if isExpectedType:
            logging.debug('Response is of expected type')
            out = open(filePath, 'wb') 
            out.write(response.content)
            out.close()
        else:
            logging.error(f"Response is not of expected type {request.expected_type}")
   

def isExpectedResponseType(response, expectedType: str) -> bool:
    responseType = response.headers.get('Content-Type')
    if responseType:
        if re.match(re.escape(expectedType), responseType):
            return True
        else:
            return False
    else:
        return None

# https://www.scrapehero.com/how-to-fake-and-rotate-user-agents-using-python-3/
def getRandomUserAgent() -> str:
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