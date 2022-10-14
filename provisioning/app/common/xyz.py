import logging
import math
import multiprocessing
import os
import re

from PIL import Image
from typing import Final, List, Tuple

from app.common.bbox import BBOX
from app.common.util import get_process_pool_count


EXTENT_LIMIT: Final = 20037508.3427892
TILE_SIZE: Final = 256
PIXELS_AT_ZOOM: Final = [
    pixels_at_zoom
    for pixels_at_zoom in [
        TILE_SIZE * pow(2, zoom) if zoom > 0 else TILE_SIZE for zoom in range(20)
    ]
]
METRES_PER_PIXEL: Final = [(EXTENT_LIMIT * 2) / pixels for pixels in PIXELS_AT_ZOOM]
METRES_PER_TILE: Final = [per_pixel * TILE_SIZE for per_pixel in METRES_PER_PIXEL]


def get_edge_tiles(tile_dir: str) -> List[str]:
    edge_tiles = list()
    for zoom_dir in [
        entry_name
        for entry_name in os.listdir(tile_dir)
        if os.path.isdir(os.path.join(tile_dir, entry_name))
    ]:
        x_dirs = list(
            map(
                lambda x_dir: str(x_dir),
                sorted(
                    [
                        int(z_entry)
                        for z_entry in os.listdir(os.path.join(tile_dir, zoom_dir))
                    ]
                ),
            )
        )
        edge_tiles += list(
            map(
                lambda y_file: os.path.join(zoom_dir, x_dirs[0], y_file),
                os.listdir(os.path.join(tile_dir, zoom_dir, x_dirs[0])),
            )
        )
        if len(x_dirs) > 1:
            edge_tiles += list(
                map(
                    lambda y_file: os.path.join(zoom_dir, x_dirs[-1], y_file),
                    os.listdir(os.path.join(tile_dir, zoom_dir, x_dirs[-1])),
                )
            )
            if len(x_dirs) > 2:
                for x_mid_dir in list(
                    map(
                        lambda x_dir_num: str(x_dir_num),
                        range(int(x_dirs[1]), int(x_dirs[-1])),
                    )
                ):
                    if os.path.exists(x_mid_dir):
                        y_file_nums = sorted(
                            [
                                int(re.sub(r"\.png", "", y_file_name))
                                for y_file_name in os.listdir(
                                    os.path.join(tile_dir, zoom_dir, x_mid_dir)
                                )
                            ]
                        )
                        edge_tiles.append(
                            os.path.join(zoom_dir, x_mid_dir, f"{y_file_nums[0]}.png")
                        )
                        if len(y_file_nums) > 1:
                            edge_tiles.append(
                                os.path.join(
                                    zoom_dir, x_mid_dir, f"{y_file_nums[-1]}.png"
                                )
                            )
    return edge_tiles


def transparent_clip_to_bbox(
    tile_paths: List[str], bbox: BBOX, quantize: bool = True
) -> None:
    logging.info("Clipping edge tiles to bbox")
    min_x, max_x, min_y, max_y = bbox.transform_as_geom("EPSG:3857").GetEnvelope()
    _transparent_clip_to_bbox_executor(
        min_x, min_y, max_x, max_y, tile_paths, quantize
    ).parallel(get_process_pool_count())


class _transparent_clip_to_bbox_executor:
    def __init__(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
        tile_paths: List[str],
        quantize: bool,
    ):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.tile_paths = tile_paths
        self.quantize = quantize

    def __call__(self, tile_path: str):
        match_groups = re.match(r".+/(\d+)/(\d+)/(\d+)\.png$", tile_path)
        z, x, y = (
            int(match_groups.group(1)),
            int(match_groups.group(2)),
            int(match_groups.group(3)),
        )
        tile_min_x = EXTENT_LIMIT * -1 + METRES_PER_TILE[z] * x
        tile_max_x = tile_min_x + METRES_PER_TILE[z]
        tile_min_y = EXTENT_LIMIT - METRES_PER_TILE[z] * (y + 1)
        tile_max_y = tile_min_y + METRES_PER_TILE[z]
        if not (
            tile_min_x >= self.max_x
            or tile_max_x <= self.min_x
            or tile_min_y >= self.max_y
            or tile_max_y <= self.min_y
        ):
            left_pixels = (
                math.floor((self.min_x - tile_min_x) / METRES_PER_PIXEL[z])
                if self.min_x > tile_min_x
                else 0
            )
            bottom_pixels = (
                math.floor((self.min_y - tile_min_y) / METRES_PER_PIXEL[z])
                if self.min_y > tile_min_y
                else 0
            )
            right_pixels = (
                math.floor((tile_max_x - self.max_x) / METRES_PER_PIXEL[z])
                if tile_max_x > self.max_x
                else 0
            )
            top_pixels = (
                math.floor((tile_max_y - self.max_y) / METRES_PER_PIXEL[z])
                if tile_max_y > self.max_y
                else 0
            )
            logging.debug(
                f"{tile_path} needs clipping by {left_pixels},{bottom_pixels} {right_pixels},{top_pixels}"
            )
            tile_src = Image.open(tile_path)
            tile = tile_src.convert("RGBA")
            for i in range(TILE_SIZE):
                for j in range(TILE_SIZE):
                    coord = (i, j)
                    if (
                        i < left_pixels
                        or i >= (TILE_SIZE - right_pixels)
                        or j < top_pixels
                        or j >= (TILE_SIZE - bottom_pixels)
                    ):
                        new_values = (0, 0, 0, 0)
                        tile.putpixel(coord, new_values)
            if self.quantize:
                tile.quantize(method=2).save(tile_path)
            else:
                tile.save(tile_path)

    def parallel(self, pool_size: int):
        pool = multiprocessing.Pool(processes=pool_size)
        pool.map(self, self.tile_paths)
        pool.close()


def merge_tiles(paths: List[Tuple[str]], quantize: bool = True) -> None:
    _merge_tiles_executor(paths, quantize).parallel(get_process_pool_count())


class _merge_tiles_executor:
    def __init__(self, paths: List[Tuple[str]], quantize: bool):
        self.paths = paths
        self.quantize = quantize

    def __call__(self, paths: Tuple[str]):
        base_path, overlay_path, output_path = paths
        overlay_image_src = overlay_image = Image.open(overlay_path)
        base_image_src = Image.open(base_path)
        overlay_image = overlay_image_src.convert("RGBA")
        base_image = base_image_src.convert("RGBA")
        for i in range(TILE_SIZE):
            for j in range(TILE_SIZE):
                coord = (i, j)
                overlay_values = overlay_image.getpixel(coord)
                if len(overlay_values) == 3:
                    overlay_values += (255,)
                if overlay_values[3] > 0:
                    base_image.putpixel(
                        coord,
                        _combine_pixels(
                            base_image.getpixel(coord) + (255,), overlay_values
                        ),
                    )
        if self.quantize:
            base_image.quantize(method=2).save(output_path)
        else:
            base_image.save(output_path)

    def parallel(self, pool_size: int):
        pool = multiprocessing.Pool(processes=pool_size)
        pool.map(self, self.paths)
        pool.close()


# https://stackoverflow.com/a/52993128/519575
def _combine_pixels(base_rgba, overlay_rgba):
    alpha = 255 - ((255 - base_rgba[3]) * (255 - overlay_rgba[3]) / 255)
    red = (
        base_rgba[0] * (255 - overlay_rgba[3]) + overlay_rgba[0] * overlay_rgba[3]
    ) / 255
    green = (
        base_rgba[1] * (255 - overlay_rgba[3]) + overlay_rgba[1] * overlay_rgba[3]
    ) / 255
    blue = (
        base_rgba[2] * (255 - overlay_rgba[3]) + overlay_rgba[2] * overlay_rgba[3]
    ) / 255
    return (int(red), int(green), int(blue), int(alpha))
