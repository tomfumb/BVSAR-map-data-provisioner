#!/bin/bash

if test -z "$PROVISIONING_HOME" 
then
      echo "This script should be run inside the Docker container. Set \$PROVISIONING_HOME to a directory location in order to proceed"
      exit 0
fi

BACKUP_DIR="$PROVISIONING_HOME"_previous
if [ -d "$BACKUP_DIR" ]; then
      echo "Removing previous backup"
      rm -rf $BACKUP_DIR
fi
CURRENT_FILE_COUNT=`ls -1 $PROVISIONING_HOME/ | wc -l`
if [ $CURRENT_FILE_COUNT -ne 0 ]; then
      echo "Backing up current code"
      cp -r $PROVISIONING_HOME $BACKUP_DIR
fi
pushd $PROVISIONING_HOME
echo "Removing current code"
rm -rf *
echo "Retrieving latest code"
git clone --depth=1 --branch=master git://github.com/tomfumb/BVSAR-map-data-provisioner .
rm -rf .git*
popd
