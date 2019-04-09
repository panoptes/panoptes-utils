#!/bin/bash -e

COMMIT_SHA=$(git rev-parse HEAD) gcloud builds submit --timeout="2h" --config cloudbuild.yaml --async .

