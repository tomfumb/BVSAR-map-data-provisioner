#!/bin/bash

pushd $(dirname ${0})/..

docker run \
    --rm \
    -w /app \
    -v ${PWD}/util/ates_to_bbox/src:/app \
    -v ${PWD}/provisioning/data/avcan-ates-areas-2020-06-23:/input \
    -v ${PWD}/util/ates_to_bbox/output:/output \
    -e KMZ_DIR_PATH=/input \
    -e GPKG_PATH=/output/areas.gpkg \
    -e FILE_BLACKLIST='["473.kmz", "474.kmz", "475.kmz", "476.kmz", "484.kmz", "485.kmz", "486.kmz", "489.kmz"]' \
    osgeo/gdal:ubuntu-full-latest \
    python -m ates_to_bbox
