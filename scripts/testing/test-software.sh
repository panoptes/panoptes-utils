#!/usr/bin/env bash

clear;

cat <<EOF
Beginning test of panoptes-utils software. This software is run inside a virtualized docker
container that has all of the required dependencies installed.

This will start a single docker container, mapping the host PANDIR=${PANDIR} into the running docker
container, which allows for testing of any local changes.

You can view the output for the tests in a separate terminal:

tail -F ${PANDIR}/logs/panoptes-testing.log

Tests will begin in 5 seconds. Press Ctrl-c to cancel.
EOF

sleep 5;

docker run --rm -it \
    -v "${PANDIR}/panoptes-utils":/var/panoptes/panoptes-utils \
    -v "${PANDIR}/logs":/var/panoptes/logs \
    panoptes-utils:develop \
    "${PANDIR}/panoptes-utils/scripts/testing/run-tests.sh"
