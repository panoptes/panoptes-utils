#!/usr/bin/env bash

docker build -f tests/Dockerfile -t panoptes-utils:testing .
docker run --rm -i -v "logs:/var/panoptes/logs" --env-file tests/env --network host panoptes-utils:testing
