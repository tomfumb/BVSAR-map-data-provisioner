from PIL import Image

def merge_xyz_tiles(base_path: str, overlay_path: str, output_path: str) -> None:
    overlay_image_src = overlay_image = Image.open(overlay_path)
    overlay_has_palette = overlay_image_src.getpalette() is not None
    base_image_src = Image.open(base_path)
    base_has_palette = base_image_src.getpalette is not None
    overlay_image = overlay_image_src.convert("RGBA") if overlay_has_palette else overlay_image_src
    base_image = base_image_src.convert("RGBA") if base_has_palette else base_image_src
    for i in range(256):
        for j in range(256):
            coord = (i,j)
            values = overlay_image.getpixel(coord)
            if values[3] > 0:
                base_image.putpixel(coord, values)
    base_image.quantize(method=2).save(output_path)
