#!/bin/bash -e

COMMIT_SHA=$(git rev-parse HEAD) gcloud builds submit --timeout="5h" --config cloudbuild.yaml --async .

