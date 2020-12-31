#!/usr/bin/env bash

clear

SLEEP_TIME=${SLEEP_TIME:-5}
PANDIR="${PANDIR:-$PWD/../../}"
PANLOG="${PANLOG:-${PANDIR}/logs}"

cat <<EOF
Beginning test of panoptes-utils software. This software is run inside a virtualized docker
container that has all of the required dependencies installed.

You can view the output for the tests in a separate terminal:

tail -F ${PANLOG}/panoptes-testing.log

Tests will begin in 5 seconds. Press Ctrl-c to cancel.
EOF

sleep "${SLEEP_TIME}"

docker run --rm -i \
  --init \
  --network "host" \
  --env-file "./tests/env" \
  -v "${PANLOG}":/var/panoptes/logs \
  panoptes-utils:develop \
  "/var/panoptes/panoptes-utils/scripts/testing/run-tests.sh"
