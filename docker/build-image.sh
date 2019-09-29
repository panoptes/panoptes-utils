#!/bin/bash -e
SOURCE_DIR="${PANDIR}/panoptes-utils"
BASE_CLOUD_FILE="cloudbuild-base-${1:-all}.yaml"
CLOUD_FILE="cloudbuild-utils-${1:-all}.yaml"

cd "${SOURCE_DIR}"

echo "Removing all __pycache__ and .pyc files before building."
find . \( -name '__pycache__' -or -name '*.pyc' \) -delete

echo "Using ${BASE_CLOUD_FILE}"
echo "Building panoptes-base!"
gcloud builds submit \
    --timeout="5h" \
    --config "${SOURCE_DIR}/docker/${BASE_CLOUD_FILE}" \
    "${SOURCE_DIR}"

echo "Using ${CLOUD_FILE}"
echo "Building panoptes-utils"
gcloud builds submit \
    --timeout="5h" \
    --config "${SOURCE_DIR}/docker/${CLOUD_FILE}" \
    "${SOURCE_DIR}"

