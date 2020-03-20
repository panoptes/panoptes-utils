#!/bin/bash -ie

USER_ID=${LOCAL_USER_ID:-9001}

# See https://denibertovic.com/posts/handling-permissions-with-docker-volumes/
echo "Starting with UID : $USER_ID"
useradd --shell /bin/zsh -u $USER_ID -o -c "PANOPTES User" -m panoptes -g panoptes -G plugdev,dialout
export HOME=/home/panoptes

# Create SSH key if it doesn't exist
SSH_KEY="${HOME}/.ssh/id_rsa"
if ! test -f "$SSH_KEY"; then
    gosu panoptes mkdir -p "${HOME}/.ssh"
    gosu panoptes ssh-keygen -q -t rsa -N "" -f "${SSH_KEY}"
fi

# Update permissions for current user.
chown -R ${USER_ID}:${USER_ID} ${HOME}
chown -R ${USER_ID}:${USER_ID} ${PANDIR}

# Authenticate if key has been set - used on local units
if [ ! -z ${GOOGLE_APPLICATION_CREDENTIALS} ]; then
    echo "Found Google credentials, activating service account."
    echo "GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"
    gosu panoptes gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
fi

# Pass arguments
exec gosu panoptes "$@"

