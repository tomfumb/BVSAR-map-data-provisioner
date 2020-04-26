#!/bin/bash

DATA_DIR=./data/bc-bulkleyvalley-bvbs
BASE_URL=http://www.bvbackpackers.ca/google-earth-maps/

mkdir -p $DATA_DIR
pushd $DATA_DIR

curl -s $BASE_URL | sed -rn 's/.*href="\/google-earth-maps\/(.*\.(KML|KMZ)).*/\1/pi' | xargs -I{} wget -nc -q $BASE_URL{}

popd
