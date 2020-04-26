#!/bin/bash

if test -z "$PROVISIONING_HOME" 
then
      echo "This script should be run inside the Docker container. Set \$PROVISIONING_HOME to a directory location in order to proceed"
      exit 0
fi

