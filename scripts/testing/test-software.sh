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
echo "Using PANDIR=${PANDIR} for docker-compose with project-directory=${PWD}"
docker run --rm -it \
  --init \
  --env-file "${PANDIR}/panoptes-utils/tests/env" \
  -v "${PANDIR}/panoptes-utils":/var/panoptes/panoptes-utils \
  -v "${PANDIR}/logs":/var/panoptes/logs \
  panoptes-utils:develop \
  "/var/panoptes/panoptes-utils/scripts/testing/run-tests.sh"
