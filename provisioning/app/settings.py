from os import path, environ

AREAS_PATH = environ.get(
    "AREAS_LOCATION", path.join(environ["DATA_LOCATION"], "areas", "areas.gpkg")
)
LOCAL_FEATURES_PATH = environ.get(
    "LOCAL_FEATURES_LOCATION",
    path.join(environ["DATA_LOCATION"], "local-features", "local-features.gpkg"),
)
