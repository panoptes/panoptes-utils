#!/bin/bash -e

SOURCE_DIR="${PANDIR}/panoptes-utils"
BASE_CLOUD_FILE="cloudbuild.yaml"

cd "${SOURCE_DIR}"

echo "Building gcr.io/panoptes-exp/panoptes-utils"
gcloud builds submit \
    --timeout="1h" \
    --config "${SOURCE_DIR}/docker/${BASE_CLOUD_FILE}" \
    "${SOURCE_DIR}"
