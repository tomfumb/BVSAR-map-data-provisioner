import os

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import Response
from gdal import Translate, Warp
from math import floor
from shutil import rmtree
from typing import Tuple
from PIL import Image
from uuid import uuid4

from api.export.export import bbox_to_xyz, georeference_raster_tile
from api.settings import TILES_DIR, TILES_PATH, PARENT_TEMP_DIR, PDF_EXPORT_MAX_PX


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
    export_tile_counts = tile_counts(x_tile_min, y_tile_min, x_tile_max, y_tile_max)
    if not tile_count_permitted(export_tile_counts[0], export_tile_counts[1]):
        raise HTTPException(
            status.HTTP_406_NOT_ACCEPTABLE,
            detail=f"Requested PDF is too big (> {PDF_EXPORT_MAX_PX}px)",
        )
    export_temp_dir = os.path.join(PARENT_TEMP_DIR, str(uuid4()))
    os.makedirs(export_temp_dir)
    tifs = list()
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
    if len(tifs) > 0:
        merge_path = os.path.join(export_temp_dir, "merge.tif")
        Warp(
            merge_path,
            tifs,
            outputBounds=(x_min, y_min, x_max, y_max),
            outputBoundsSRS="EPSG:4326",
            dstSRS="EPSG:3857",
        )
        pdf_path = os.path.join(export_temp_dir, "merge.pdf")
        Translate(pdf_path, merge_path, format="PDF")
        with open(pdf_path, "rb") as pdf_file:
            pdf_data = pdf_file.read()
        rmtree(export_temp_dir)
        return Response(pdf_data, media_type="application/pdf")
    else:
        rmtree(export_temp_dir)
        return None


def tile_counts(
    x_tile_min: int, y_tile_min: int, x_tile_max: int, y_tile_max: int
) -> Tuple[int]:
    return ((x_tile_max - x_tile_min) + 1, (y_tile_max - y_tile_min) + 1)


def tile_count_permitted(x_tile_count: int, y_tile_count: int) -> bool:
    return (x_tile_count * 256) * (y_tile_count * 256) < PDF_EXPORT_MAX_PX
