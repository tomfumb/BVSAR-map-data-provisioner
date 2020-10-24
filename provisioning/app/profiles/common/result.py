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
        for idx, edge_tile in enumerate(existing_edge_tiles):
            logging.debug(
                f"Stitching edge tile {idx + 1} of {len(existing_edge_tiles)} to prior output {edge_tile}"
            )
            new_edge_tile_path = os.path.join(source_dir, edge_tile)
            merge_tiles(
                os.path.join(dest_dir, edge_tile),
                new_edge_tile_path,
                new_edge_tile_path,
            )

    logging.info("Updating result directories with latest export")
    merge_dirs(source_dir, dest_dir)
