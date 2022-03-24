import logging
import math
import os
import re
import time
import wget

from ftplib import FTP
from typing import Final

from app.common.util import get_cache_path


MAX_ITERATIONS: Final = 3


def retrieve_directory(domain: str, path: str) -> str:
    file_list = []
    iteration = 0
    while iteration < MAX_ITERATIONS:
        if iteration > 0:
            delay = math.pow(1000, iteration) / 1000
            logging.info(
                f"Iteration {iteration + 1} for failing FTP requests, sleep for {delay}s before retry..."
            )
            time.sleep(delay)
            logging.info("...resuming")
        cache_path = None
        try:
            ftp = FTP(domain)
            ftp.login()
            ftp.cwd(path)
            ftp.retrlines("LIST", lambda x: file_list.append(x.split()))
            ftp.close()
            for info in file_list:
                ls_type, name = info[0], info[-1]
                if not ls_type.startswith("d"):
                    cache_path = _cache_path(domain, path, name)
                    cache_directory = os.path.dirname(cache_path)
                    if not os.path.exists(cache_directory):
                        os.mkdir(cache_directory)
                    else:
                        fetch(name, domain, path, cache_path)
            print("")
            return cache_directory
        except Exception as e:
            logging.error(f"Error retrieving resources over FTP: {e}")
            if cache_path and os.path.exists(cache_path):
                os.remove(cache_path)
            iteration += 1

    if iteration == MAX_ITERATIONS - 1:
        logging.error(
            f"Unable to retrieve resources over FTP after {iteration + 1} iteration(s), exiting"
        )
        exit(1)


def fetch(file_name: str, domain: str, path: str, destination_path: str = None):
    if destination_path is None:
        destination_path = _cache_path(domain, path, file_name)
    if not os.path.exists(destination_path):
        wget.download(
            f"ftp://{domain}{path}/{file_name}", out=destination_path,
        )
    return destination_path

def _cache_path(domain: str, path: str, file_name: str) -> str:
    return os.path.join(get_cache_path(
        (re.sub(r"[^a-z0-9\.]", "", f"{domain}{path}", flags=re.IGNORECASE),)
    ), file_name)