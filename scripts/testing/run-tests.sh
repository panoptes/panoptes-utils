#!/bin/bash -e

REPORT_FILE=${REPORT_FILE:-build/coverage.xml}

export PYTHONPATH="${PYTHONPATH}:${PANDIR}/panoptes-utils/scripts/testing/coverage"
export COVERAGE_PROCESS_START="${PANDIR}/panoptes-utils/setup.cfg"

coverage erase

# Run coverage over the pytest suite
echo "Starting tests"
coverage run "$(command -v pytest)"

echo "Combining coverage"
coverage combine

echo "Making XML coverage report at ${REPORT_FILE}"
coverage xml -o "${REPORT_FILE}"

exit 0
