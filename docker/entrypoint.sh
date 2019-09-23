#!/bin/bash -ie

# Create SSH key if it doesn't exist
SSH_KEY="${HOME}/.ssh/id_rsa"
if ! test -f "$SSH_KEY"; then
    ssh-keygen -t rsa -N "" -f "${SSH_KEY}"
fi


METADATA_URL='http://metadata.google.internal/computeMetadata/v1/project/attributes'

# Authenticate if key has been set - used on local units
if [ ! -z ${GOOGLE_APPLICATION_CREDENTIALS} ]; then
    echo "Found Google credentials, activating service account."
    echo "GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"
    /root/google-cloud-sdk/bin/gcloud auth activate-service-account \
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
    /root/conda/envs/panoptes-env/bin/python ${PANDIR}/panoptes-utils/scripts/connect_cloud_sql_proxy.py \
        --config="${HOME}/.cloud-sql-conf.yaml" \
        --verbose &
fi

# Pass arguments
exec "$@"
