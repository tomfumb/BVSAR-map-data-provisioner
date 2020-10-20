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
            overlay_values = overlay_image.getpixel(coord)
            if len(overlay_values) == 3:
                overlay_values += (255,)
            if overlay_values[3] > 0:
                base_image.putpixel(coord, combine_pixels(base_image.getpixel(coord) + (255,), overlay_values))
    base_image.quantize(method=2).save(output_path)


# https://stackoverflow.com/a/52993128/519575
def combine_pixels(base_rgba, overlay_rgba):
    alpha = 255 - ((255 - base_rgba[3]) * (255 - overlay_rgba[3]) / 255)
    red   = (base_rgba[0] * (255 - overlay_rgba[3]) + overlay_rgba[0] * overlay_rgba[3]) / 255
    green = (base_rgba[1] * (255 - overlay_rgba[3]) + overlay_rgba[1] * overlay_rgba[3]) / 255
    blue  = (base_rgba[2] * (255 - overlay_rgba[3]) + overlay_rgba[2] * overlay_rgba[3]) / 255
    return (int(red), int(green), int(blue), int(alpha))