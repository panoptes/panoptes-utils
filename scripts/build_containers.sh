#!/bin/bash -e
SOURCE_DIR=${PANDIR}/panoptes-utils

if [[ $* == *--base* ]]; then
	echo "Build base!"
	gcloud builds submit --timeout="5h" --config "${SOURCE_DIR}/docker/cloudbuild-base.yaml" "${SOURCE_DIR}"
fi

echo "Build Utils"
gcloud builds submit --timeout="5h" --config "${SOURCE_DIR}/docker/cloudbuild-utils.yaml" --async "${SOURCE_DIR}"

