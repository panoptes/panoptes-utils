#!/bin/bash -e

echo "Setting up base environment"

# Authenticate if key has been set - used on local units
if [ ! -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "Found Google credentials, activating service account"
    /root/google-cloud-sdk/bin/gcloud auth activate-service-account \
    --key-file="$GOOGLE_APPLICATION_CREDENTIALS"
fi

# Authenticate if on GCE
if [ ! -z "$CLOUDSDK_COMPUTE_ZONE" ]; then
    echo "Starting Cloud SQL proxy"
    python ${PANDIR}/panoptes-utils/scripts/connect_cloud_sql_proxy.py \
        --config="${PANDIR}/panoptes-utils/docker/cloud-sql-conf.yaml" \
        --verbose &

    echo "Getting DB passwords from metadata server"
    curl --silent "http://metadata.google.internal/computeMetadata/v1/project/attributes/pgpass" -H "Metadata-Flavor: Google" > $HOME/.pgpass
    chmod 600 $HOME/.pgpass
fi

# Pass arguments
exec "$@"
