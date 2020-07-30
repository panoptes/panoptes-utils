#!/bin/bash -e

PANOPTES_UTILS=${PANOPTES_UTILS:-$PANDIR/panoptes-utils}

cd "${PANOPTES_UTILS}"

# In the local develop we need to pass git to the docker build context.
sed -i s'/^\.git$/\!\.git/' .dockerignore

echo "Building local panoptes-utils:develop"
docker build \
  --force-rm \
  -t "panoptes-utils:develop" \
  -f "${PANOPTES_UTILS}/docker/develop.Dockerfile" \
  "${PANOPTES_UTILS}"

# Revert our .dockerignore changes.
sed -i s'/^!\.git$/\.git/' .dockerignore

cat <<EOF
Done building the local images.

To run the tests enter:

scripts/testing/test-software.sh
EOF
