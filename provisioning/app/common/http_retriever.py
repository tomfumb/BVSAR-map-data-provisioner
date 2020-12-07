import re
import os
import random
import math
import requests
import time
import logging

from aiohttp import request as aiorequest
from asyncio import get_event_loop, Lock
from pydantic import BaseModel
from typing import List, Final

from app.common.util import asyncio_with_concurrency


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
        if i > 0 and i % 1000 == 0:
            logging.info(log_format.format(i))
        if requests.head(request.url).status_code != 200:
            logging.warn(f"{request.url} does not exist")
    logging.info(log_format.format(len(check_requests)))


def retrieve(
    retrieval_requests: List[RetrievalRequest], max_concurrency: int = 1
) -> None:
    if len(retrieval_requests) == 0:
        return
    requests_remaining = retrieval_requests.copy()
    requests_failed = list()
    iteration = 0
    requests_executed = 0
    requests_executed_lock = Lock()

    async def execute(request: RetrievalRequest) -> None:
        nonlocal requests_executed
        url = request.url
        filePath = request.path
        os.makedirs(os.path.dirname(filePath), exist_ok=True)
        logging.debug(f"Requesting {filePath} from {url}")
        try:
            async with requests_executed_lock:
                remaining_count = len(requests_remaining) - requests_executed

            if (
                remaining_count <= 10
                or math.ceil(len(requests_remaining) / 10) % remaining_count == 0
            ):
                logging.info(f"{remaining_count} remaining")

            async with aiorequest(
                "get", url, headers={"User-Agent": get_random_user_agent()}
            ) as response:
                is_expected_type = is_expected_response_type(
                    response, request.expected_type
                )
                if is_expected_type is None:
                    logging.info(
                        f"Cannot determine response type, may not be the desired response for {url}"
                    )
                else:
                    if is_expected_type:
                        logging.debug(f"Response is of expected type for {url}")
                        out = open(filePath, "wb")
                        out.write(await response.read())
                        out.close()
                    else:
                        raise ValueError(f"Response for {url} is not the expected type")
        except Exception as ex:
            logging.debug(f"Error fetching {url}: {ex}")
            requests_failed.append(request)
        finally:
            async with requests_executed_lock:
                requests_executed += 1

    while iteration < MAX_REQUEST_ITERATION:
        requests_executed = 0
        logging.info(
            f"Requesting {len(requests_remaining)} resource(s) over HTTP in iteration {iteration + 1} of {MAX_REQUEST_ITERATION}"
        )
        if iteration > 0:
            delay = math.pow(1000, iteration) / 1000
            logging.info(
                f"Iteration {iteration + 1} for failing HTTP requests, sleep for {delay}s before retry..."
            )
            time.sleep(delay)
            logging.info("...resuming")
        async_requests = [execute(each) for each in requests_remaining]
        get_event_loop().run_until_complete(
            asyncio_with_concurrency(max_concurrency, async_requests)
        )
        if len(requests_failed) > 0:
            logging.info(
                f"{len(requests_failed)} of {len(retrieval_requests)} requests failed in iteration {iteration + 1}"
            )
            requests_remaining = requests_failed.copy()
            requests_failed.clear()
            iteration += 1
        else:
            return


def is_expected_response_type(response, expectedType: str) -> bool:
    responseType = response.headers.get("Content-Type")
    if responseType:
        if re.match(re.escape(expectedType), responseType):
            return True
        else:
            return False
    else:
        return None


# https://www.scrapehero.com/how-to-fake-and-rotate-user-agents-using-python-3/
def get_random_user_agent() -> str:
    userAgentList = (
        # Chrome
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
        "Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
        # Firefox
        "Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)",
        "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)",
        "Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)",
        "Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
        "Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
        "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)",
        "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)",
        "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)",
    )
    return random.choice(userAgentList)
