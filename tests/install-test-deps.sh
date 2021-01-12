#!/usr/bin/env bash

apt-get update
apt-get install --no-install-recommends --yes \
  wait-for-it \
  bzip2 ca-certificates gcc pkg-config \
  libffi-dev libssl-dev \
  astrometry.net astrometry-data-tycho2-08 astrometry-data-tycho2-10-19 \
  dcraw exiftool libcfitsio-dev libcfitsio-bin \
  libfreetype6-dev libpng-dev libjpeg-dev libffi-dev \
  git
