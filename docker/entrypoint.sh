#!/bin/bash -ie

USER_ID=${LOCAL_USER_ID:-1000}

# See https://denibertovic.com/posts/handling-permissions-with-docker-volumes/
if [ "${USER_ID}" != 1000 ]; then
    echo "Starting with UID : $USER_ID"
    # Modify panoptes default group.
    addgroup --gid "${USER_ID}" panoptes-docker
    usermod --gid "${USER_ID}"
    # Change permissions
    chown -R "${USER_ID}:${USER_ID}" "${PANDIR}"
    chown -R "${USER_ID}:${USER_ID}" "/home/panoptes"
    chown -R "${USER_ID}:${USER_ID}" "/astrometry"
fi

# Authenticate if key has been set - used on local units
if [ -n "${GOOGLE_APPLICATION_CREDENTIALS}" ]; then
    echo "Found Google credentials, activating service account."
    echo "GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"
    gosu panoptes gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
fi

# Pass arguments
exec gosu panoptes "$@"

