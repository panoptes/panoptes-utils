#!/usr/bin/bash

export PYTHONPATH="${PYTHONPATH}:${PANDIR}/panoptes-utils/scripts/testing/coverage"
export COVERAGE_PROCESS_START="${PANDIR}/panoptes-utils/setup.cfg"

coverage erase

# Run coverage over the pytest suite
echo "Starting tests"
coverage run "$(command -v pytest)"

exit 0
