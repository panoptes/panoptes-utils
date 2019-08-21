#!/bin/bash -e
SOURCE_DIR="${PANDIR}/panoptes-utils"
BASE_CLOUD_FILE="cloudbuild-base-${1:-all}.yaml"
CLOUD_FILE="cloudbuild-utils-${1:-all}.yaml"

echo "Using ${CLOUD_FILE}"

if [[ $* == *--base* ]]; then
	echo "Building panoptes-base!"
	gcloud builds submit \
        --timeout="5h" \
        --config "${SOURCE_DIR}/docker/${BASE_CLOUD_FILE}" \
        "${SOURCE_DIR}"
fi

echo "Building panoptes-utils"
gcloud builds submit \
    --timeout="5h" \
    --config "${SOURCE_DIR}/docker/${CLOUD_FILE}" \
    --async "${SOURCE_DIR}"

