#!/usr/bin/env bash

clear

PANLOG="${PANLOG:-/tmp/panoptes/logs}"

cat <<EOF
Beginning test of panoptes-utils software. This software is run inside a virtualized docker
container that has all of the required dependencies installed.

You can view the output for the tests in a separate terminal:

tail -F ${PANLOG}/panoptes-testing.log

Tests will begin in 5 seconds. Press Ctrl-c to cancel.
EOF

SLEEP_TIME=${1:-5}

sleep "${SLEEP_TIME}"

# Create a directory for storing log files and coverage reports.
mkdir -p "${BUILD_DIR}" && chmod 777 "${BUILD_DIR}"
echo "Set ${BUILD_DIR}"
ls -la .
docker-compose -f docker/docker-compose-testing.yaml up

echo "Build dir output"
ls -la .
ls -la "${BUILD_DIR}"
