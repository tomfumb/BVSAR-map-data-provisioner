import logging
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from gdal import Translate, Warp
from math import floor
from shutil import rmtree
from typing import Tuple
from PIL import Image
from uuid import uuid4

from api.export.export import bbox_to_xyz, georeference_raster_tile, tile_edges
from api.settings import TILES_DIR, TILES_PATH, PARENT_TEMP_DIR, PDF_EXPORT_MAX_TILES


router = APIRouter()


@router.get("/info/{zoom}/{x_min}/{y_min}/{x_max}/{y_max}/{profile}")
async def export_info(
    profile: str, zoom: int, x_min: float, y_min: float, x_max: float, y_max: float
):
    export_tile_bounds = bbox_to_xyz(x_min, x_max, y_min, y_max, zoom)
    export_tile_counts = tile_counts(*export_tile_bounds)
    return {
        "z": zoom,
        "x_tiles": export_tile_counts[0],
        "y_tiles": export_tile_counts[1],
        "sample": f"{TILES_PATH}/{profile}/{zoom}/{export_tile_bounds[0] + floor(export_tile_counts[0] / 2)}/{export_tile_bounds[1] + floor(export_tile_counts[1] / 2)}.png",
        "permitted": tile_count_permitted(export_tile_counts[0], export_tile_counts[1]),
    }


@router.get("/pdf/{zoom}/{x_min}/{y_min}/{x_max}/{y_max}/{profile}")
async def export_pdf(
    profile: str, zoom: int, x_min: float, y_min: float, x_max: float, y_max: float
):
    x_tile_min, y_tile_min, x_tile_max, y_tile_max = bbox_to_xyz(
        x_min, x_max, y_min, y_max, zoom
    )
    check_tile_count_permitted(
        *tile_counts(x_tile_min, y_tile_min, x_tile_max, y_tile_max)
    )
    try:
        export_temp_dir = os.path.join(PARENT_TEMP_DIR, str(uuid4()))
        os.makedirs(export_temp_dir)
        tifs = list()
        logging.info("Georeferencing tiles")
        for x in range(x_tile_min, x_tile_max + 1):
            for y in range(y_tile_min, y_tile_max + 1):
                src_png_path = os.path.join(
                    TILES_DIR, profile, str(zoom), str(x), f"{y}.png"
                )
                if os.path.exists(src_png_path):
                    tif_path = os.path.join(export_temp_dir, f"{zoom}_{x}_{y}.tif")
                    png_image = Image.open(src_png_path)
                    georeference_raster_tile(
                        x, y, zoom, src_png_path, tif_path, png_image.mode == "P"
                    )
                    tifs.append(tif_path)
        logging.info(f"Gereferenced {len(tifs)} tiles")
        if len(tifs) > 0:
            merge_path = os.path.join(export_temp_dir, "merge.tif")
            logging.info(f"Merging to {merge_path}")
            Warp(
                merge_path,
                tifs,
                outputBounds=(x_min, y_min, x_max, y_max),
                outputBoundsSRS="EPSG:4326",
                dstSRS="EPSG:3857",
            )
            logging.info("Merge complete")
            pdf_path = os.path.join(export_temp_dir, "merge.pdf")
            logging.info(f"Translating to {pdf_path}")
            Translate(pdf_path, merge_path, format="PDF")
            logging.info("Translate complete")
            logging.info(
                f"Reading PDF data to memory ({os.stat(pdf_path).st_size} bytes)"
            )
            with open(pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
            logging.info("Deleting temp directory")
            rmtree(export_temp_dir)
            logging.info("Deleted")
            return Response(pdf_data, media_type="application/pdf")
        else:
            logging.info("Deleting temp directory")
            rmtree(export_temp_dir)
            logging.info("Deleted")
            return None
    except Exception as e:
        logging.error(f"Warp failed with {e}")
        rmtree(export_temp_dir)
        return None


@router.get("/pdf/v2/{zoom}/{x_min}/{y_min}/{x_max}/{y_max}/{profile}")
async def export_pdf_v2(
    profile: str, zoom: int, x_min: float, y_min: float, x_max: float, y_max: float
):
    x_tile_min, y_tile_min, x_tile_max, y_tile_max = bbox_to_xyz(
        x_min, x_max, y_min, y_max, zoom
    )
    export_tile_counts = tile_counts(x_tile_min, y_tile_min, x_tile_max, y_tile_max)
    check_tile_count_permitted(export_tile_counts[0], export_tile_counts[1])
    try:
        export_temp_dir = os.path.join(PARENT_TEMP_DIR, str(uuid4()))
        os.makedirs(export_temp_dir)
        png_merge_path = os.path.join(export_temp_dir, "merge.png")
        png_merge_image = Image.new(
            "RGBA", (export_tile_counts[0] * 256, export_tile_counts[1] * 256)
        )
        src_tile_count = 0
        logging.info(f"Expecting {export_tile_counts[0]}x{export_tile_counts[1]} tiles")
        for x in range(x_tile_min, x_tile_max + 1):
            for y in range(y_tile_min, y_tile_max + 1):
                src_png_path = os.path.join(
                    TILES_DIR, profile, str(zoom), str(x), f"{y}.png"
                )
                if os.path.exists(src_png_path):
                    src_tile_count += 1
                    src_png_image = Image.open(src_png_path)
                    if src_png_image.mode == "P":
                        src_png_image = src_png_image.convert("RGBA")
                    logging.info(f"pasting {src_png_path}")
                    png_merge_image.paste(
                        src_png_image,
                        (
                            (x - x_tile_min) * 256 + (1 if x > 0 else 0),
                            (y - y_tile_min) * 256 + (1 if y > 0 else 0),
                        ),
                    )
        # not currently quantizing as not thought necessary for tiff conversion
        logging.info(f"useful tiles: {src_tile_count}")
        if src_tile_count > 0:
            logging.info("Saving merged png")
            png_merge_image.save(png_merge_path)
            tif_merge_path = os.path.join(export_temp_dir, "merge.tif")
            ul_bounds = tile_edges(x_tile_min, y_tile_min, zoom)
            lr_bounds = tile_edges(x_tile_max, y_tile_max, zoom)
            logging.info(
                f"Translate to {tif_merge_path} from {png_merge_path} for {ul_bounds[0]}, {ul_bounds[1]}, {lr_bounds[2]}, {lr_bounds[3]}"
            )
            Translate(
                tif_merge_path,
                png_merge_path,
                **{
                    "outputSRS": "EPSG:4326",
                    "outputBounds": [
                        ul_bounds[0],
                        ul_bounds[1],
                        lr_bounds[2],
                        lr_bounds[3],
                    ],
                },
            )
            tif_warp_path = os.path.join(export_temp_dir, "warp.tif")
            logging.info(f"Warp to {tif_warp_path} from {tif_merge_path}")
            Warp(
                tif_warp_path,
                tif_merge_path,
                outputBounds=(x_min, y_min, x_max, y_max),
                outputBoundsSRS="EPSG:4326",
                dstSRS="EPSG:3857",
            )
            pdf_path = os.path.join(export_temp_dir, "output.pdf")
            logging.info(f"Translate to {pdf_path} from {tif_warp_path}")
            Translate(pdf_path, tif_warp_path, format="PDF")
            logging.info("Reading PDF to memory")
            with open(pdf_path, "rb") as pdf_file:
                pdf_data = pdf_file.read()
            logging.info("Removing intermediary files")
            rmtree(export_temp_dir)
            logging.info("Returning data")
            return Response(pdf_data, media_type="application/pdf")
        else:
            rmtree(export_temp_dir)
            return None
    except Exception as e:
        logging.error(f"Warp failed with {e}")
        rmtree(export_temp_dir)
        return None


def tile_counts(
    x_tile_min: int, y_tile_min: int, x_tile_max: int, y_tile_max: int
) -> Tuple[int]:
    return ((x_tile_max - x_tile_min) + 1, (y_tile_max - y_tile_min) + 1)


def check_tile_count_permitted(x_tile_count: int, y_tile_count: int) -> None:
    if not tile_count_permitted(x_tile_count, y_tile_count):
        raise HTTPException(
            418, detail=f"Requested PDF is too big (> {PDF_EXPORT_MAX_TILES} tiles)",
        )


def tile_count_permitted(x_tile_count: int, y_tile_count: int) -> bool:
    return x_tile_count * y_tile_count <= PDF_EXPORT_MAX_TILES
