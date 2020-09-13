#!/usr/bin/env bash
set -e

TAG="${TAG:-develop}"
PANDIR="${PANDIR:-$PWD/../}"
PANOPTES_UTILS="${PANOPTES_UTILS:-${PANDIR}/panoptes-utils}"

INCLUDE_BASE="${INCLUDE_BASE:-false}"
BASE_IMAGE_URL="${BASE_IMAGE_URL:-gcr.io/panoptes-exp/panoptes-base:latest}"

echo "Setting up local environment in ${PANOPTES_UTILS}"
cd "${PANOPTES_UTILS}"

build_base() {
  echo "Building local panoptes-base:${TAG} in ${PANOPTES_UTILS}"
  docker build \
    --force-rm \
    --build-arg "userid=$(id -u)" \
    -t "panoptes-base:${TAG}" \
    -f "${PANOPTES_UTILS}/docker/base/Dockerfile" \
    "${PANOPTES_UTILS}"

  # Use our local base for build below.
  BASE_IMAGE_URL="panoptes-base:${TAG}"
  echo "Setting BASE_IMAGE_URL=${BASE_IMAGE_URL}"
}

build_develop() {
  echo "Building local panoptes-utils:${TAG} from ${BASE_IMAGE_URL} in ${PANOPTES_UTILS}"
  docker build \
    --build-arg "userid=$(id -u),image_url=${BASE_IMAGE_URL}" \
    -t "panoptes-utils:${TAG}" \
    -f "${PANOPTES_UTILS}/docker/Dockerfile" \
    "${PANOPTES_UTILS}"
}

####################################################################################
# Script logic below
####################################################################################

if [ "${INCLUDE_BASE}" = true ]; then
  build_base
fi

build_develop

cat <<EOF
Done building the local images.

To run the tests enter:

scripts/testing/test-software.sh
EOF
