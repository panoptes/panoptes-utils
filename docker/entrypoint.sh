#!/bin/bash -ie

USER_ID=${LOCAL_USER_ID:-9001}

# See https://denibertovic.com/posts/handling-permissions-with-docker-volumes/
echo "Starting with UID : $USER_ID"
useradd --shell /bin/zsh -u $USER_ID -o -c "PANOPTES User" -m panoptes -g panoptes -G panoptes
export HOME=/home/panoptes

# Create SSH key if it doesn't exist
SSH_KEY="${HOME}/.ssh/id_rsa"
if ! test -f "$SSH_KEY"; then
    mkdir -p "${HOME}/.ssh"
    ssh-keygen -q -t rsa -N "" -f "${SSH_KEY}"
    chown -R ${USER_ID}:${USER_ID} ${HOME}/.ssh
fi

METADATA_URL='http://metadata.google.internal/computeMetadata/v1/project/attributes'

# Authenticate if key has been set - used on local units
if [ ! -z ${GOOGLE_APPLICATION_CREDENTIALS} ]; then
    echo "Found Google credentials, activating service account."
    echo "GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"
    gcloud auth activate-service-account \
    --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
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
