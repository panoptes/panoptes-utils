#!/usr/bin/env bash
set -e

COVERAGE_REPORT_FILE=${COVERAGE_REPORT_FILE:-/var/panoptes/logs/coverage.xml}

# This assumes we are always running in a docker container.
export COVERAGE_PROCESS_START="/var/panoptes/panoptes-utils/setup.cfg"

coverage erase

echo "Checking to make sure panoptes-config-server is running"
scripts/wait-for-it.sh --timeout 30 \
  --strict panoptes-config-server:8765 \
  -- \
  echo "Found panoptes-config-server, starting tests."

# Run coverage over the pytest suite.
coverage run "$(command -v pytest)"

echo "Combining coverage"
coverage combine

echo "Making XML coverage report at ${COVERAGE_REPORT_FILE}"
coverage xml -o "${COVERAGE_REPORT_FILE}"
coverage report --show-missing

exit 0
