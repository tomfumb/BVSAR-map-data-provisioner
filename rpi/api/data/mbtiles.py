import logging
import os
from sqlite3 import Connection, connect
from time import time
from threading import Lock
from api.settings import TILES_DIR


connections = dict()
cache_lock = Lock()


def get_connection(profile_name: str) -> Connection:
    return connections.get(profile_name)


def cache_connections():
    with cache_lock:
        for dirname in os.listdir(TILES_DIR):
            dirpath = os.path.join(TILES_DIR, dirname)
            if os.path.isdir(dirpath):
                try:
                    if dirname not in connections:
                        mbtiles_path = os.path.join(
                            TILES_DIR, dirname, f"{dirname}.mbtiles"
                        )
                        if not os.path.exists(mbtiles_path):
                            raise FileNotFoundError()
                        conn_start = time()
                        connections[dirname] = connect(mbtiles_path)
                        logging.debug(
                            f"{dirname} established in {time() - conn_start}s"
                        )
                except FileNotFoundError as e:
                    logging.warning(
                        f"Unable to establish mbtiles connection for {dirname}: {e}"
                    )
