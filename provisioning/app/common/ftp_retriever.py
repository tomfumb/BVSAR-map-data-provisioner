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
    cache_directory = get_cache_path(
        (re.sub(r"[^a-z0-9\.]", "", f"{domain}{path}", flags=re.IGNORECASE),)
    )
    if not os.path.exists(cache_directory):
        os.mkdir(cache_directory)
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
        destination_path = None
        try:
            ftp = FTP(domain)
            ftp.login()
            ftp.cwd(path)
            ftp.retrlines("LIST", lambda x: file_list.append(x.split()))
            ftp.close()
            for info in file_list:
                ls_type, name = info[0], info[-1]
                if not ls_type.startswith("d"):
                    destination_path = os.path.join(cache_directory, name)
                    if os.path.exists(destination_path):
                        logging.debug(f"Already have {name}, ignoring")
                    else:
                        _fetch(name, destination_path, domain, path)
            print("")
            return cache_directory
        except Exception as e:
            logging.error(f"Error retrieving resources over FTP: {e}")
            if destination_path and os.path.exists(destination_path):
                os.remove(destination_path)
            iteration += 1

    if iteration == MAX_ITERATIONS - 1:
        logging.error(
            f"Unable to retrieve resources over FTP after {iteration + 1} iteration(s), exiting"
        )
        exit(1)


def _fetch(file_name: str, destination_path: str, domain: str, path: str):
    wget.download(
        f"ftp://{domain}{path}/{file_name}",
        out=destination_path,
        bar=wget.bar_thermometer,
    )
