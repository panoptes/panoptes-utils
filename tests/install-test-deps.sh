#!/usr/bin/env bash

sudo apt-get update
sudo apt-get install --no-install-recommends \
  wait-for-it \
  bzip2 ca-certificates gcc pkg-config \
  libffi-dev libssl-dev \
  astrometry.net astrometry-data-tycho2-08 \
  dcraw exiftool libcfitsio-dev libcfitsio-bin \
  libfreetype6-dev libpng-dev libjpeg-dev libffi-dev
