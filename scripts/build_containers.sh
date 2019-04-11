#!/bin/bash -e
SOURCE_DIR=${PANDIR}/panoptes-utils

gcloud builds submit --timeout="5h" --config ${SOURCE_DIR}/cloudbuild.yaml --async ${SOURCE_DIR}

