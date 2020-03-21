#!/bin/bash -e
SOURCE_DIR="${PANDIR}/panoptes-utils"
BASE_CLOUD_FILE="cloudbuild.yaml"

cd "${SOURCE_DIR}"

echo "Using ${BASE_CLOUD_FILE}"
echo "Building panoptes-utils"
gcloud builds submit \
    --timeout="5h" \
    --config "${SOURCE_DIR}/docker/${BASE_CLOUD_FILE}" \
    "${SOURCE_DIR}"
