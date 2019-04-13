#!/bin/bash -e 

source /opt/conda/etc/profile.d/conda.sh
conda activate panoptes-env
export PYTHONPATH="$PYTHONPATH:$PANDIR/panoptes-utils/scripts/testing/coverage"
export COVERAGE_PROCESS_START=${PANDIR}/panoptes-utils/.coveragerc
coverage run $(which pytest) -v --test-databases all
coverage combine
bash <(curl -s https://codecov.io/bash)