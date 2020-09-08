#!/usr/bin/env bash

clear

SLEEP_TIME=${SLEEP_TIME:-5}
TEMPDIR="${TEMPDIR:-./tmp}"
PANLOG="${PANLOG:-/var/panoptes/logs}"

cat <<EOF
Beginning test of panoptes-utils software. This software is run inside a virtualized docker
container that has all of the required dependencies installed.

You can view the output for the tests in a separate terminal:

tail -F ${PANLOG}/panoptes-testing.log

Tests will begin in 5 seconds. Press Ctrl-c to cancel.
EOF

sleep "${SLEEP_TIME}"

echo "Making temp directory for testing."
mkdir -p "${TEMPDIR}" && chmod -R 777 "${TEMPDIR}"
ls -laR .
docker-compose -f docker/docker-compose-testing.yaml up
ls -laR .
