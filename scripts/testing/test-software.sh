#!/usr/bin/env bash

clear

SLEEP_TIME=${SLEEP_TIME:-5}
export PANDIR="${PANDIR:-/var/panoptes}"
export PANLOG="${PANLOG:-${PANDIR}/logs}"

cat <<EOF
Beginning test of panoptes-utils software. This software is run inside a virtualized docker
container that has all of the required dependencies installed.

You can view the output for the tests in a separate terminal:

tail -F ${PANLOG}/panoptes-testing.log

Tests will begin in 5 seconds. Press Ctrl-c to cancel.
EOF

sleep "${SLEEP_TIME}"

echo "Running tests with $(id)"
mkdir -p logs && chmod 777 logs
echo "Using PANDIR=${PANDIR} for docker-compose with project-directory=${PWD}"
docker-compose --project-directory "${PWD}" -f docker/docker-compose-testing.yaml up
# TODO send appropriate failure signal if error.
