#!/usr/bin/env bash

PANOPTES_CONFIG_FILE="tests/testing.yaml"
PANOPTES_CONFIG_HOST="localhost"
PANOPTES_CONFIG_PORT="8765"

echo "Starting config server in background"
panoptes-config-server --verbose run --no-load-local --no-save-local &

echo "Checking to make sure panoptes-config-server is running"
wait-for-it --timeout=30 --strict "${PANOPTES_CONFIG_HOST}:${PANOPTES_CONFIG_PORT}" -- echo "Config-server up"

echo "Starting testing"
pytest

echo "Stopping config server"
panoptes-config-server --verbose stop

exit 0
