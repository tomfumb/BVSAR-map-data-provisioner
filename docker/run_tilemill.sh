#!/bin/bash

$TILEMILL_HOME/index.js --server=true --listenHost=${LISTEN_HOST:-0.0.0.0} --coreUrl=${CORE_URL:-0.0.0.0:20009} --tileUrl=${TILE_URL:-0.0.0.0:20008}
