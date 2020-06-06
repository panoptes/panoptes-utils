#!/bin/bash -e

export PYTHONPATH="${PYTHONPATH}:/var/panoptes/panoptes-utils/scripts/testing/coverage"
export COVERAGE_PROCESS_START="/var/panoptes/panoptes-utils/setup.cfg"

coverage erase

# Run coverage over the pytest suite
echo "Starting tests"
coverage run "$(command -v pytest)"

exit 0
