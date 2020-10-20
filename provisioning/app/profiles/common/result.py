import logging
import os
import re

from typing import List

from app.common.util import merge_dirs
from app.common.merge_xyz_tiles import merge_xyz_tiles


def add_or_update(source_dir: str, dest_dir: str):
    logging.info("Searching existing tiles for edge overlaps and stitching if necessary")
    edge_tiles = list()
    for zoom_dir in [entry_name for entry_name in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, entry_name))]:
        x_dirs = list(map(lambda x_dir: str(x_dir), sorted([int(z_entry) for z_entry in os.listdir(os.path.join(source_dir, zoom_dir))])))
        edge_tiles += list(map(lambda y_file: os.path.join(zoom_dir, x_dirs[0], y_file), os.listdir(os.path.join(source_dir, zoom_dir, x_dirs[0]))))
        if len(x_dirs) > 1:
            edge_tiles += list(map(lambda y_file: os.path.join(zoom_dir, x_dirs[-1], y_file), os.listdir(os.path.join(source_dir, zoom_dir, x_dirs[-1]))))
            if len(x_dirs) > 2:
                for x_mid_dir in list(map(lambda x_dir_num: str(x_dir_num), range(int(x_dirs[1]), int(x_dirs[-1])))):
                    y_file_nums = sorted([int(re.sub(r"\.png", "", y_file_name)) for y_file_name in os.listdir(os.path.join(source_dir, zoom_dir, x_mid_dir))])
                    edge_tiles.append(os.path.join(zoom_dir, x_mid_dir, f"{y_file_nums[0]}.png"))
                    if len(y_file_nums) > 1:
                        edge_tiles.append(os.path.join(zoom_dir, x_mid_dir, f"{y_file_nums[-1]}.png"))
    existing_edge_tiles = [edge_tile for edge_tile in edge_tiles if os.path.exists(os.path.join(dest_dir, edge_tile))]
    if len(existing_edge_tiles) > 0:
        logging.info(f"Stitching {len(existing_edge_tiles)} tile(s)")
        for idx, edge_tile in enumerate(existing_edge_tiles):
            logging.debug(f"Stitching edge tile {idx + 1} of {len(existing_edge_tiles)} to prior output {edge_tile}")
            new_edge_tile_path = os.path.join(source_dir, edge_tile)
            merge_xyz_tiles(os.path.join(dest_dir, edge_tile), new_edge_tile_path, new_edge_tile_path)

    logging.info("Updating result directories with latest export")
    merge_dirs(source_dir, dest_dir)
