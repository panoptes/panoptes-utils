#!/usr/bin/env bash

clear

SLEEP_TIME=${SLEEP_TIME:-5}
PANLOG="${PANLOG:-/var/panoptes/logs}"

cat <<EOF
Beginning test of panoptes-utils software. This software is run inside a virtualized docker
container that has all of the required dependencies installed.

You can view the output for the tests in a separate terminal:

tail -F ${PANLOG}/panoptes-testing.log

Tests will begin in 5 seconds. Press Ctrl-c to cancel.
EOF

sleep "${SLEEP_TIME}"

ls -l ./tmp
docker-compose -f docker/docker-compose-testing.yaml up
ls -l ./tmp
