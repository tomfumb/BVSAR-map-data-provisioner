import re
import os
import sys
import random
import math
import requests
import time
import logging

from pydantic import BaseModel
from typing import List, Final

from concurrent import futures
from timeit import default_timer as timer


MAX_REQUEST_ITERATION: Final = 3


class RetrievalRequest(BaseModel):
    path: str
    url: str
    expected_type: str

class ExistsCheckRequest(BaseModel):
    url: str

def check_exists(check_requests: List[ExistsCheckRequest]) -> None:
    logging.info(f"Issuing {len(check_requests)} HEAD requests...")
    log_format = "... {0}"
    for i, request in enumerate(check_requests):
        if i > 0 and i % 1000 == 0: logging.info(log_format.format(i))
        if requests.head(request.url).status_code != 200:
            logging.warn(f"{request.url} does not exist")
    logging.info(log_format.format(len(check_requests)))


def retrieve(retrieval_requests: List[RetrievalRequest]):
    requests_remaining = retrieval_requests.copy()
    requests_failed = list()
    iteration = 0
    while iteration < MAX_REQUEST_ITERATION:
        logging.info(f"Requesting {len(requests_remaining)} resource(s) over HTTP in iteration {iteration + 1} of {MAX_REQUEST_ITERATION}")
        if iteration > 0:
            delay = math.pow(1000, iteration) / 1000
            logging.info(f"Iteration {iteration + 1} for failing HTTP requests, sleep for {delay}s before retry...")
            time.sleep(delay)
            logging.info("...resuming")
        while len(requests_remaining) > 0:
            if len(retrieval_requests) >= 10 and len(requests_remaining) % round(len(retrieval_requests) / 10) == 0:
                logging.info(f"{len(requests_remaining)} remaining")
            request = requests_remaining.pop(0)
            url = request.url
            filePath = request.path
            os.makedirs(os.path.dirname(filePath), exist_ok = True)
            logging.debug(f"Requesting {filePath} from {url}")
            try:
                response = requests.get(url, headers = { "User-Agent": getRandomUserAgent() })
                isExpectedType = isExpectedResponseType(response, request.expected_type)
                if isExpectedType is None:
                    logging.info(f"Cannot determine response type, may not be the desired response for {url}")
                else:
                    if isExpectedType:
                        logging.debug(f"Response is of expected type for {url}")
                        out = open(filePath, "wb") 
                        out.write(response.content)
                        out.close()
                    else:
                        raise ValueError(f"Response for {url} is not the expected type")
            except Exception as ex:
                logging.debug(f"Error fetching {url}: {ex}")
                requests_failed.append(request)
        if len(requests_failed) > 0:
            logging.info(f"{len(requests_failed)} of {len(retrieval_requests)} requests failed in iteration {iteration + 1}")
            requests_remaining = requests_failed.copy()
            requests_failed.clear()
            iteration += 1
        else:
            return


# def httpRetriever(retrieval_requests: List[RetrievalRequest], maxConcurrentRequests: int = 10):
#     requests = retrieval_requests.copy()
#     if len(requests) > 0:
#         bestTimePerRequest = sys.maxsize
#         bestConcurrency = 1
#         concurrency = 1
#         while concurrency <= maxConcurrentRequests:
#             logging.debug(f"Testing request speed with {concurrency} concurrent requests")
#             bestConcurrency = concurrency
#             numRequestsToTest = min(concurrency, len(requests))
#             logging.debug(f"Got {numRequestsToTest} requests to test with")
#             if numRequestsToTest > 0:
#                 testRequests = requests[:numRequestsToTest]
#                 del requests[:numRequestsToTest]
#                 start = timer()
#                 with futures.ThreadPoolExecutor(max_workers = numRequestsToTest) as executor:
#                     executeRequests(executor, testRequests)
#                 end = timer()
#                 testTimePerRequest = (end - start) / numRequestsToTest
#                 logging.debug(f"Time per request {testTimePerRequest}")
#                 if testTimePerRequest < bestTimePerRequest:
#                     logging.debug('Got new best time')
#                     bestTimePerRequest = testTimePerRequest
#                 else:
#                     bestConcurrency = concurrency - 1
#                     logging.debug(f"Previous time per request was better, exit and use {bestConcurrency}")
#                     break
#                 concurrency += 1
#             else:
#                 break
        
#         logging.info(f"Issuing requests with {bestConcurrency} concurrency")
#         with futures.ThreadPoolExecutor(max_workers = bestConcurrency) as executor:
#             executeRequests(executor, requests)


# def executeRequests(executor, requests: List[RetrievalRequest]) -> None:
#     requestFutures = (executor.submit(issueFileRequest, request) for request in requests)
#     for future in futures.as_completed(requestFutures):
#         try:
#             future.result()
#         except Exception as exc:
#             logging.info(f'Exception: {type(exc)}')


# def issueFileRequest(request: RetrievalRequest):
#     filePath = request.path
#     os.makedirs(os.path.dirname(filePath), exist_ok = True)
#     url = request.url
#     logging.info(f'Requesting {filePath} from {url}')
#     response = requests.get(url, headers = { 'User-Agent': getRandomUserAgent() })
#     isExpectedType = isExpectedResponseType(response, request.expected_type)
#     if isExpectedType is None:
#         logging.info('Cannot determine response type, may not be the desired response')
#     else:
#         if isExpectedType:
#             logging.debug('Response is of expected type')
#             out = open(filePath, 'wb') 
#             out.write(response.content)
#             out.close()
#         else:
#             logging.error(f"Response is not of expected type {request.expected_type}")
   

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