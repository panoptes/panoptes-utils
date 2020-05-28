#!/bin/bash -e

REPORT_FILE=${REPORT_FILE:-coverage.xml}

export PYTHONPATH="${PYTHONPATH}:/var/panoptes/panoptes-utils/scripts/testing/coverage"
export COVERAGE_PROCESS_START="/var/panoptes/panoptes-utils/setup.cfg"

coverage erase

# Run coverage over the pytest suite
echo "Starting tests"
coverage run "$(command -v pytest)" -x -vv -rfes --test-databases all

echo "Combining coverage"
coverage combine

echo "Making XML coverage report at ${REPORT_FILE}"
coverage xml -o "${REPORT_FILE}"

exit 0
