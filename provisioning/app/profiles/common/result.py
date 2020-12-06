import logging
import os

from app.common.util import merge_dirs
from app.common.xyz import get_edge_tiles, merge_tiles


def add_or_update(source_dir: str, dest_dir: str):
    logging.info(
        "Searching existing tiles for edge overlaps and stitching if necessary"
    )
    edge_tiles = get_edge_tiles(source_dir)
    existing_edge_tiles = [
        edge_tile
        for edge_tile in edge_tiles
        if os.path.exists(os.path.join(dest_dir, edge_tile))
    ]
    if len(existing_edge_tiles) > 0:
        logging.info(f"Stitching {len(existing_edge_tiles)} tile(s)")
        path_tuples = [
            (
                os.path.join(dest_dir, edge_tile),
                os.path.join(source_dir, edge_tile),
                os.path.join(source_dir, edge_tile),
            )
            for edge_tile in existing_edge_tiles
        ]
        merge_tiles(path_tuples)

    logging.info("Updating result directories with latest export")
    merge_dirs(source_dir, dest_dir)
