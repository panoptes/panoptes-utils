#!/bin/bash -e

export PYTHONPATH="$PYTHONPATH:$PANDIR/panoptes-utils/scripts/testing/coverage"
export COVERAGE_PROCESS_START="${PANDIR}/panoptes-utils/setup.cfg"

# Run coverage over the pytest suite
echo "Staring tests"
coverage run "$(command -v pytest)" -x -vv -rfes --test-databases all

echo "Combining coverage"
coverage combine

coverage xml

exit 0
