#!/bin/bash

if test -z "$PROVISIONING_HOME" 
then
      echo "This script should be run inside the Docker container. Set \$PROVISIONING_HOME to a directory location in order to proceed"
      exit 0
fi

pushd $PROVISIONING_HOME
pushd ..
BACKUP_DIR="$PROVISIONING_HOME"_previous
echo "Removing previous backup if it exists"
rm -rf cd $BACKUP_DIR
echo "Backing up current code"
mv $PROVISIONING_HOME $BACKUP_DIR
echo "Retrieving latest code"
git clone --depth=1 --branch=master git://github.com/tomfumb/BVSAR-map-data-provisioner $PROVISIONING_HOME
rm -rf $PROVISIONING_HOME/.git*
