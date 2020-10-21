import logging
import os
import re

from ftplib import FTP

from app.common.util import get_cache_path


def retrieve_directory(domain: str, path: str) -> str:
    cache_directory = get_cache_path(
        (re.sub(r"[^a-z0-9\.]", "", f"{domain}{path}", flags=re.IGNORECASE),)
    )
    if not os.path.exists(cache_directory):
        os.mkdir(cache_directory)
    ftp = FTP(domain)
    ftp.login()
    ftp.cwd(path)
    file_list = []
    ftp.retrlines("LIST", lambda x: file_list.append(x.split()))

    def fetch(file_name: str, destination_path: str, remote_size: int):
        logging.info(f"Downloading {name} ({remote_size} bytes)")
        with open(destination_path, "wb") as f:
            ftp.retrbinary(f"RETR {name}", f.write)

    for info in file_list:
        ls_type, remote_size, name = info[0], int(info[2]), info[-1]
        if not ls_type.startswith("d"):
            destination_path = os.path.join(cache_directory, name)
            if os.path.exists(destination_path):
                local_size = os.stat(destination_path).st_size
                if local_size != remote_size:
                    logging.info(
                        f"Local {name} is incorrect size, retrieving again {local_size}/{remote_size}"
                    )
                    fetch(name, destination_path, remote_size)
                else:
                    logging.debug(f"Already have {name}, ignoring")
            else:
                fetch(name, destination_path, remote_size)
    ftp.close()
    return cache_directory
