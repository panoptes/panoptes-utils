#!/bin/bash -e

cd "${PANDIR}/panoptes-utils"

pip install --ignore-installed pip PyYAML
# Install any updated requirements
pip install -r requirements.txt

# Install module
pip install -e ".[all]"

export PYTHONPATH="$PYTHONPATH:$PANDIR/panoptes-utils/scripts/testing/coverage"
export COVERAGE_PROCESS_START="${PANDIR}/panoptes-utils/.coveragerc"
coverage run "$(command -v pytest)" -vv -rfes --test-databases all

# Upload coverage reports if running from Travis.
if [[ $TRAVIS ]]; then
	coverage combine
	bash <(curl -s https://codecov.io/bash)
fi

exit 0
