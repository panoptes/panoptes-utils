#!/bin/bash -e
SOURCE_DIR=${PANDIR}/panoptes-utils

gcloud builds submit --timeout="5h" --config ${SOURCE_DIR}/cloudbuild-base.yaml ${SOURCE_DIR}

gcloud builds submit --timeout="5h" --config ${SOURCE_DIR}/cloudbuild-utils.yaml ${SOURCE_DIR}

