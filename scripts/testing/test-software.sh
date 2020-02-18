#!/bin/bash -e

clear;

cat << EOF
Beginning test of panoptes-utils software.  This will start a single docker container, mapping the
host $PANDIR into the running docker container, which allows for testing of any local changes.

You can view the output for the tests in a separate terminal:

grc tail -F ${PANDIR}/log/pytest-all.log

The tests will start by updating: ${PANDIR}/panoptes-utils/requirements.txt

Tests will begin in 5 seconds. Press Ctrl-c to cancel.
EOF

sleep 5;

docker run --rm -it \
    -e LOCAL_USER_ID=$(id -u) \
    -v /var/panoptes/panoptes-utils:/var/panoptes/panoptes-utils \
    gcr.io/panoptes-survey/panoptes-utils \
    "${PANDIR}/panoptes-utils/scripts/testing/run-tests.sh"

