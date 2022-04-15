import logging
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from osgeo import osr
from osgeo.gdal import Translate
from math import floor
from shutil import rmtree
from typing import Tuple
from uuid import uuid4

from api.export.export import bbox_to_xyz, latlon_to_xyz, bbox_to_pixels
from api.settings import TILES_PATH, PARENT_TEMP_DIR, PDF_EXPORT_MAX_TILES, FILES_DIR
from api.util import get_name_for_bounds


export_dir = os.path.join(FILES_DIR, "PDF Exports")
os.makedirs(export_dir, exist_ok=True)

router = APIRouter()


@router.get("/info/{zoom}/{x_min}/{y_min}/{x_max}/{y_max}/{profile}")
async def export_info(
    profile: str, zoom: int, x_min: float, y_min: float, x_max: float, y_max: float
):
    sample_tile = [
        str(floor(val))
        for val in latlon_to_xyz(
            y_min + (y_max - y_min) / 2, x_min + (x_max - x_min) / 2, zoom
        )
    ]
    export_tile_bounds = bbox_to_xyz(x_min, x_max, y_min, y_max, zoom)
    export_tile_counts = tile_counts(*export_tile_bounds)
    pixel_counts = bbox_to_pixels(x_min, x_max, y_min, y_max, zoom)
    return {
        "z": zoom,
        "x_px": pixel_counts[0],
        "y_px": pixel_counts[1],
        "sample": f"{TILES_PATH}/{profile}/{zoom}/{'/'.join(sample_tile)}.png",
        "permitted": tile_count_permitted(export_tile_counts[0], export_tile_counts[1]),
        "name": export_name(profile, zoom, x_min, y_min, x_max, y_max),
    }


def export_name(
    profile: str, zoom: int, x_min: float, y_min: float, x_max: float, y_max: float
):
    return f"{get_name_for_bounds(f'{profile}-{zoom}', x_min, y_min, x_max, y_max)}.pdf"


@router.get("/pdf/{zoom}/{x_min}/{y_min}/{x_max}/{y_max}/{profile}")
async def export_pdf(
    profile: str,
    zoom: int,
    x_min: float,
    y_min: float,
    x_max: float,
    y_max: float,
):
    pdf_mime_type = "application/pdf"
    pdf_file_path = os.path.join(
        export_dir,
        f"{get_name_for_bounds(f'{profile}-{zoom}', x_min, y_min, x_max, y_max)}.pdf",
    )

    def read_pdf():
        with open(pdf_file_path, "rb") as pdf_file:
            return pdf_file.read()

    if os.path.exists(pdf_file_path):
        return Response(read_pdf(), media_type=pdf_mime_type)

    export_temp_dir = os.path.join(PARENT_TEMP_DIR, str(uuid4()))
    os.makedirs(export_temp_dir)
    xml_file_path = os.path.join(export_temp_dir, "gdal.xml")
    # Hack for development purposes:
    # While debugging via dev server you will likely only have a single thread that can only handle one HTTP request at a time
    # In this scenario if tile requests for PDF export go to localhost:port for the dev server you will see a deadlock. The export process waits for tile HTTP requests to complete and tile requests cannot complete until the export process returns.
    # If you have a separate device serving the same tiles, use this device's domain for PDF_EXPORT_TILE_HOST
    # If you do not have a separate device, start a simple web server container (e.g. httpd) to serve the same tiles and enter that localhost:port for PDF_EXPORT_TILE_HOST
    tile_host = os.environ.get("PDF_EXPORT_TILE_HOST", "localhost")
    base_url = f"http://{tile_host}"
    with open(xml_file_path, "w") as xml_file:
        xml_file.write(
            f"""<GDAL_WMS>
    <Service name="TMS">
        <ServerUrl>{base_url}/tile/file/{profile}/${{z}}/${{x}}/${{y}}.png</ServerUrl>
    </Service>
    <DataWindow>
        <UpperLeftX>-20037508.34</UpperLeftX>
        <UpperLeftY>20037508.34</UpperLeftY>
        <LowerRightX>20037508.34</LowerRightX>
        <LowerRightY>-20037508.34</LowerRightY>
        <TileLevel>{zoom}</TileLevel>
        <TileCountX>1</TileCountX>
        <TileCountY>1</TileCountY>
        <YOrigin>top</YOrigin>
    </DataWindow>
    <Projection>EPSG:3857</Projection>
    <BlockSizeX>256</BlockSizeX>
    <BlockSizeY>256</BlockSizeY>
    <BandsCount>3</BandsCount>
    <ZeroBlockHttpCodes>204,404</ZeroBlockHttpCodes>
</GDAL_WMS>"""
        )
    bbox_srs = osr.SpatialReference()
    bbox_srs.SetFromUserInput("EPSG:4326")
    try:
        result = Translate(
            pdf_file_path,
            xml_file_path,
            format="PDF",
            projWin=[x_min, y_max, x_max, y_min],
            projWinSRS=bbox_srs,
        )
        print(result)
    except Exception as ex:
        print(ex)
    pdf_data = read_pdf()
    logging.info("Deleting temp directory")
    rmtree(export_temp_dir)
    return Response(pdf_data, media_type=pdf_mime_type)


def tile_counts(
    x_tile_min: int, y_tile_min: int, x_tile_max: int, y_tile_max: int
) -> Tuple[int]:
    return ((x_tile_max - x_tile_min) + 1, (y_tile_max - y_tile_min) + 1)


def check_tile_count_permitted(x_tile_count: int, y_tile_count: int) -> None:
    if not tile_count_permitted(x_tile_count, y_tile_count):
        raise HTTPException(
            418,
            detail=f"Requested PDF is too big (> {PDF_EXPORT_MAX_TILES} tiles)",
        )


def tile_count_permitted(x_tile_count: int, y_tile_count: int) -> bool:
    return x_tile_count * y_tile_count <= PDF_EXPORT_MAX_TILES
