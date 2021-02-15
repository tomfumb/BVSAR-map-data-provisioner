from math import log, tan, radians, cos, pi, floor, pow


"""Some parts adapted from https://github.com/jimutt/tiles-to-tiff"""


AXIS_EXTENT = 20037508.3427892 * 2
TILES_PER_ZOOM = [1 * pow(2, zoom) for zoom in range(23)]
TILE_SIZE = 256


def bbox_to_pixels(lon_min, lon_max, lat_min, lat_max, z):
    x_degrees_per_pixel = (360 / TILES_PER_ZOOM[z]) / TILE_SIZE
    y_degrees_per_pixel = (180 / TILES_PER_ZOOM[z]) / TILE_SIZE
    return (
        round((lon_max - lon_min) / x_degrees_per_pixel),
        round((lat_max - lat_min) / y_degrees_per_pixel),
    )


def sec(x):
    return 1 / cos(x)


def latlon_to_xyz(lat, lon, z):
    tile_count = pow(2, z)
    x = (lon + 180) / 360
    y = (1 - log(tan(radians(lat)) + sec(radians(lat))) / pi) / 2
    return (tile_count * x, tile_count * y)


def bbox_to_xyz(lon_min, lon_max, lat_min, lat_max, z):
    x_min, y_max = latlon_to_xyz(lat_min, lon_min, z)
    x_max, y_min = latlon_to_xyz(lat_max, lon_max, z)
    return (floor(x_min), floor(y_min), floor(x_max), floor(y_max))
