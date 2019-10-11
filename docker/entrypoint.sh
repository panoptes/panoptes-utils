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

# Update home permissions
chown -R ${USER_ID}:${USER_ID} $HOME

# We always want to update the requirements because it is assumed the container
# will run with the local directory mapped and that may have changed.
if test -f requirements.txt; then
    gosu panoptes pip install --no-cache-dir -q -r requirements.txt
    gosu panoptes pip install --no-cache-dir -q -e .
fi

METADATA_URL='http://metadata.google.internal/computeMetadata/v1/project/attributes'

# Authenticate if key has been set - used on local units
if [ ! -z ${GOOGLE_APPLICATION_CREDENTIALS} ]; then
    echo "Found Google credentials, activating service account."
    echo "GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"
    gosu panoptes gcloud auth activate-service-account --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
fi

# Authenticate if on GCE
if [ ! -z ${GOOGLE_COMPUTE_INSTANCE} ]; then
    echo "Looks like this is a GCE instance."
    echo "Getting Cloud SQL config from metadata server"
    curl --silent "${METADATA_URL}/cloud_sql_conf" -H "Metadata-Flavor: Google" > ${HOME}/.cloud-sql-conf.yaml

    echo "Getting DB passwords from metadata server"
    curl --silent "${METADATA_URL}/pgpass" -H "Metadata-Flavor: Google" > ${HOME}/.pgpass
    chmod 600 ${HOME}/.pgpass

    echo "Starting Cloud SQL proxy"
    python ${PANDIR}/panoptes-utils/scripts/connect_cloud_sql_proxy.py \
        --config="${HOME}/.cloud-sql-conf.yaml" \
        --verbose &
fi

# Pass arguments
exec gosu panoptes "$@"
