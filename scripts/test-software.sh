#!/usr/bin/env bash

clear

SLEEP_TIME=${SLEEP_TIME:-5}
PANDIR="${PANDIR:-$PWD/../}"
PANLOG="${PANLOG:-${PANDIR}/logs}"
BUILD_DIR="${PANDIR}/panoptes-utils"
IMAGE_NAME="${IMAGE_NAME:-panoptes-utils}"
TAG="${TAG:-testing}"

cat <<EOF
Beginning test of panoptes-utils software. This software is run inside a virtualized docker
container that has all of the required dependencies installed.

You can view the output for the tests in a separate terminal:

tail -F ${PANLOG}/panoptes-testing.log

Tests will begin in 5 seconds. Press Ctrl-c to cancel.
EOF

sleep "${SLEEP_TIME}"

# Build testing image (if necessary).
docker build \
  -f "${BUILD_DIR}/tests/Dockerfile" \
  -t "${IMAGE_NAME}:${TAG}" "${BUILD_DIR}"

# Run the tests in docker container.
docker run --rm -it \
  --network "host" \
  --env-file "${BUILD_DIR}/tests/env" \
  --volume "${PANLOG}:/var/panoptes/logs" \
  "${IMAGE_NAME}:${TAG}"
