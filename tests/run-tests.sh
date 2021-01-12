#!/usr/bin/env bash
set -e

COVERAGE_REPORT_FILE="coverage.xml"
PANOPTES_CONFIG_FILE="tests/testing.yaml"
PANOPTES_CONFIG_HOST="localhost"
PANOPTES_CONFIG_PORT="8765"

# This assumes we are always running in a docker container.
export COVERAGE_PROCESS_START="/var/panoptes/panoptes-utils/setup.cfg"

coverage erase

# Run coverage over the pytest suite.
echo "Starting config server in background"
panoptes-config-server --verbose run --no-load-local --no-save-local &

echo "Checking to make sure panoptes-config-server is running"
wait-for-it --timeout=30 --strict "${PANOPTES_CONFIG_HOST}:${PANOPTES_CONFIG_PORT}" -- echo "Config-server up"

echo "Starting testing"
pytest
echo "Stopping config server"
panoptes-config-server --verbose stop

#echo "Combining coverage for ${COVERAGE_REPORT_FILE}"
#coverage combine

#echo "Making XML coverage report at ${COVERAGE_REPORT_FILE}"
#coverage xml -o "${COVERAGE_REPORT_FILE}"
#coverage report --show-missing

exit 0
