#!/bin/bash -ie

# Authenticate if key has been set - used on local units
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
    echo "Found Google credentials, activating service account."
    echo "GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"
    gosu panoptes gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
fi

# Pass arguments
exec gosu panoptes "$@"

