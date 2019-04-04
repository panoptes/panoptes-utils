#!/bin/bash -e

usage() {
  echo -n "##################################################
# Start the config param server.
# 
# This will start a docker container running the config server.
##################################################
 $ $(basename $0)
 
 Example:
  ./start_docker_config_server.sh
"
}

docker run --rm -d\
    --name config_server \
    --network host \
    -v /var/panoptes:/var/panoptes \
    gcr.io/panoptes-survey/panoptes-utils \
    python3 scripts/run_config_server.py --public