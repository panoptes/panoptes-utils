#!/bin/bash -e

COMMIT_SHA=$(git rev-parse HEAD) gcloud builds submit --timeout="1h" --config cloudbuild.yaml .

