#!/bin/bash -ie

echo "Starting panoptes container"
# Pass arguments
exec gosu panoptes "$@"
