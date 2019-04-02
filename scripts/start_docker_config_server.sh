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

if [ $# -eq 0 ]; then
    usage
    exit 1
fi

docker run --rm \
	--name config_server \
	-p 6563:6563 \
	-v /var/panoptes:/var/panoptes \
	gcr.io/panoptes-survey/panoptes-utils \
	python3 scripts/run_config_server.py --public
	