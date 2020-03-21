#!/bin/bash -ie

USER_ID=${LOCAL_USER_ID:-1000}

# See https://denibertovic.com/posts/handling-permissions-with-docker-volumes/
if [ "${USER_ID}" != 1000 ]; then
    echo "Starting with UID : $USER_ID"
    useradd --shell /bin/zsh --uid "${USER_ID}" -c "PANOPTES Docker User" -MN -G plugdev,dialout,panoptes
    export HOME=/home/panoptes
fi

# Authenticate if key has been set - used on local units
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
    echo "Found Google credentials, activating service account."
    echo "GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"
    gosu panoptes gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
fi

# Pass arguments
exec gosu panoptes "$@"

