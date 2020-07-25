#!/bin/bash -e

TAG="${1:-latest}"
PLATFORMS="${2:-linux/amd64}"

SOURCE_DIR="${PANDIR}/panoptes-utils"
BASE_CLOUD_FILE="cloudbuild.yaml"

cd "${SOURCE_DIR}"

echo "Building gcr.io/panoptes-exp/panoptes-utils:${TAG} in ${SOURCE_DIR}"
gcloud builds submit \
    --timeout="5h" \
    --substitutions="_TAG=${TAG},_PLATFORMS=${PLATFORMS}" \
    --config "${SOURCE_DIR}/docker/${BASE_CLOUD_FILE}" \
    "${SOURCE_DIR}"

