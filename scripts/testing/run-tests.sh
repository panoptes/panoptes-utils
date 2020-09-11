#!/usr/bin/env bash
set -e

COVERAGE_REPORT_FILE=${COVERAGE_REPORT_FILE:-/var/panoptes/logs/coverage.xml}

# This assumes we are always running in a docker container.
export COVERAGE_PROCESS_START="/var/panoptes/panoptes-utils/setup.cfg"

coverage erase

echo "Figure out where we are: ${PWD}"
echo "Figure out PATH: ${PATH}"

echo "Checking to make sure panoptes-config-server is running"
scripts/wait-for-it.sh --timeout=30 --strict panoptes-config-server:8765 -- echo "Found panoptes-config-server, starting tests."

id
ls -la

# Run coverage over the pytest suite.
echo "Starting config server"
coverage run "panoptes-config-server --verbose run"
echo "Starting testing"
coverage run "$(command -v pytest)"
echo "Stopping config server"
coverage run "panoptes-config-server --verbose stop"

echo "Combining coverage for ${COVERAGE_REPORT_FILE}"
coverage combine

ls -la
echo "Making XML coverage report at ${COVERAGE_REPORT_FILE}"
coverage xml -o "${COVERAGE_REPORT_FILE}"
coverage report --show-missing

exit 0
