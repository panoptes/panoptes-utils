#!/usr/bin/env bash

echo "Preparing tests"
docker build --quiet -f tests/Dockerfile -t panoptes-utils:testing .
docker run --rm -i -v "logs:/var/panoptes/logs" --env-file tests/env --network host panoptes-utils:testing
