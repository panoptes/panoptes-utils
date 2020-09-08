#!/usr/bin/env bash

set -e

clear

BUILD_DIR="${BUILD_DIR:-../../build}"
PANLOG="${PANLOG:-/var/panoptes/logs}"

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
docker-compose -f docker/docker-compose-testing.yaml up

echo "Build dir output"
ls -la "${BUILD_DIR}"
