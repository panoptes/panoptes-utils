#!/bin/bash -e
SOURCE_DIR="${PANDIR}/panoptes-utils"
BASE_CLOUD_FILE="cloudbuild-base-amd64.yaml"

cd "${SOURCE_DIR}"

echo "Using ${BASE_CLOUD_FILE}"
echo "Building panoptes-utils!"
gcloud builds submit \
    --async \
    --config "${SOURCE_DIR}/docker/${BASE_CLOUD_FILE}" \
    "${SOURCE_DIR}"
