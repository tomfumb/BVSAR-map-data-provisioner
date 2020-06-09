#!/bin/bash

if [ -z "$PROVISIONED_DATA" ]; then
	DATA_BASE_DIR=./data
else
	DATA_BASE_DIR=$PROVISIONED_DATA
fi

DATA_DIR=$DATA_BASE_DIR/bc-trim-20000
BASE_URL=https://pub.data.gov.bc.ca/datasets/177864/tif/bcalb/

mkdir -p $DATA_DIR
pushd $DATA_DIR

curl -s $BASE_URL | sed -rn 's/.*>([0-9]{2,3}[a-z])\/<.*/\1/p' | while read area
do
	curl -s $BASE_URL$area/ | sed -rn 's/.*>([0-9A-Z]+\.zip)<.*/\1/p' | while read file
	do
		wget $BASE_URL$area/$file
	done
	ls -1 *.zip | xargs -I{} unzip {}
	rm *.zip
done

# gdalwarp --config GDAL_CACHEMAX 8000 -wm 8000 -r lanczos -t_srs EPSG:3857 -srcnodata 0 -multi -wo NUM_THREADS=ALL_CPUS bc-trim-*.tiff bc-trim-area2-20000-3857.tiff

popd
