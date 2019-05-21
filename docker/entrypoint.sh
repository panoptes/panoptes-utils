#!/bin/bash -e

echo "Setting up base environment"
echo "GOOGLE_APPLICATION_CREDENTIALS: ${GOOGLE_APPLICATION_CREDENTIALS}"
echo "GOOGLE_COMPUTE_INSTANCE: ${GOOGLE_COMPUTE_INSTANCE}"

# Authenticate if key has been set - used on local units
if [ ! -z ${GOOGLE_APPLICATION_CREDENTIALS} ]; then
    echo "Found Google credentials, activating service account"
    /root/google-cloud-sdk/bin/gcloud auth activate-service-account \
    --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
fi

# Authenticate if on GCE
if [ ! -z ${GOOGLE_COMPUTE_INSTANCE} ]; then
    echo "Getting Cloud SQL config from metadata server"
    curl --silent "http://metadata.google.internal/computeMetadata/v1/project/attributes/cloud_sql_conf" -H "Metadata-Flavor: Google"
    curl --silent "http://metadata.google.internal/computeMetadata/v1/project/attributes/cloud_sql_conf" -H "Metadata-Flavor: Google" > ${HOME}/.cloud-sql-conf.yaml

    echo "Getting DB passwords from metadata server"
    curl --silent "http://metadata.google.internal/computeMetadata/v1/project/attributes/pgpass" -H "Metadata-Flavor: Google" > ${HOME}/.pgpass
    chmod 600 ${HOME}/.pgpass

    echo "Cloud SQL conf:"
    cat ${HOME}/.cloud-sql-conf.yaml

    echo "Starting Cloud SQL proxy"
    python ${PANDIR}/panoptes-utils/scripts/connect_cloud_sql_proxy.py \
        --config="${HOME}/.cloud-sql-conf.yaml" \
        --verbose &
fi

# Pass arguments
exec "$@"
