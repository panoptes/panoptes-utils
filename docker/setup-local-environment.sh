#!/usr/bin/env bash

set -e

INCLUDE_BASE=${INCLUDE_BASE:-false}
PANOPTES_UTILS=${PANOPTES_UTILS:-$PANDIR/panoptes-utils}
_IMAGE_URL="gcr.io/panoptes-exp/panoptes-base:latest"

cd "${PANOPTES_UTILS}"

build_base() {
  echo "Building local panoptes-base:develop in ${PANOPTES_UTILS}"
  docker build \
    --force-rm \
    -t "panoptes-base:develop" \
    -f "${PANOPTES_UTILS}/docker/base.Dockerfile" \
    "${PANOPTES_UTILS}"

  # Use our local base for build below.
  _IMAGE_URL="panoptes-base:develop"
}

build_develop() {
  echo "Building local panoptes-utils:develop from ${_IMAGE_URL} in ${PANOPTES_UTILS}"
  docker build \
    --force-rm \
    --build-arg="image_url=${_IMAGE_URL}" \
    --build-arg="pip_install=." \
    -t "panoptes-utils:develop" \
    -f "${PANOPTES_UTILS}/docker/Dockerfile" \
    "${PANOPTES_UTILS}"
}

if [ "${INCLUDE_BASE}" ]; then
  build_base
fi

build_develop

cat <<EOF
Done building the local images.

To run the tests enter:

scripts/testing/test-software.sh
EOF
