#!/bin/bash -e

cd "${PANDIR}/panoptes-utils"

# Install any updated requirements
pip install -r requirements.txt

export PYTHONPATH="$PYTHONPATH:$PANDIR/panoptes-utils/scripts/testing/coverage"
export COVERAGE_PROCESS_START=.coveragerc
coverage run "$(command -v pytest)" -vvrs --test-databases all

# Upload coverage reports if running from Travis.
if [[ $TRAVIS ]]; then
	coverage combine
	bash <(curl -s https://codecov.io/bash)
fi

exit 0
