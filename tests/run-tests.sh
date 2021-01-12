#!/usr/bin/env bash

export PANOPTES_CONFIG_FILE="tests/testing.yaml"
export PANOPTES_CONFIG_HOST="localhost"
export PANOPTES_CONFIG_PORT="8765"
export PANLOG="logs"

echo "Starting config server in background"
panoptes-config-server --verbose \
  --host "${PANOPTES_CONFIG_HOST}" \
  --port "${PANOPTES_CONFIG_PORT}" \
  run \
  --config-file "${PANOPTES_CONFIG_FILE}" \
  --no-load-local --no-save-local &

echo "Checking to make sure panoptes-config-server is running"
wait-for-it --timeout=30 --strict "${PANOPTES_CONFIG_HOST}:${PANOPTES_CONFIG_PORT}" -- echo "Config-server up"

echo "Starting testing"
pytest

echo "Stopping config server"
panoptes-config-server --verbose \
  --host "${PANOPTES_CONFIG_HOST}" \
  --port "${PANOPTES_CONFIG_PORT}" \
  stop

exit 0
