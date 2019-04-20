#!/bin/bash -e 

export PYTHONPATH="$PYTHONPATH:$PANDIR/panoptes-utils/scripts/testing/coverage"
export COVERAGE_PROCESS_START=${PANDIR}/panoptes-utils/.coveragerc
coverage run $(which pytest) -v --test-databases all

# Upload coverage reports if running from Travis.
if [[ $TRAVIS ]]; then
	coverage combine
	bash <(curl -s https://codecov.io/bash)
fi
