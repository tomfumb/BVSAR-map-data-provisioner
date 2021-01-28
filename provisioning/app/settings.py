import os

AREAS_PATH = os.environ.get("AREAS_LOCATION", "/tiledata/areas/areas.gpkg")
LOCAL_FEATURES_PATH = os.environ.get(
    "LOCAL_FEATURES_LOCATION", "/tiledata/local-features/local-features.gpkg"
)
