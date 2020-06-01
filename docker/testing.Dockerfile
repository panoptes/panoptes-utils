ARG base_image=python:3.8-slim-buster

FROM $base_image AS base-image
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"
ARG astrometry_dir="/astrometry/data"
ARG cr2_url="https://storage.googleapis.com/panoptes-resources/test-data/canon.cr2"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/zsh

ENV PANDIR $pan_dir
ENV PANLOG "$pan_dir/logs"
ENV POCS $pocs_dir
ENV SOLVE_FIELD /usr/bin/solve-field

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget curl bzip2 ca-certificates \
        astrometry.net sextractor dcraw exiftool libcfitsio-dev libcfitsio-bin imagemagick \
        libfreetype6-dev libpng-dev fonts-lato libsnappy-dev \
        gcc git pkg-config && \
    # Create directories
    mkdir -p ${POCS} && \
    mkdir -p ${PANDIR}/logs && \
    mkdir -p ${PANDIR}/images && \
    mkdir -p ${PANDIR}/panoptes-utils && \
    # Astrometry folders
    mkdir -p "${astrometry_dir}" && \
    echo "add_path ${astrometry_dir}" >> /etc/astrometry.cfg

COPY ./requirements.txt /tmp/requirements.txt
# First deal with pip and PyYAML - see https://github.com/pypa/pip/issues/5247
RUN pip install --no-cache-dir --no-deps --ignore-installed pip PyYAML && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Install module
COPY . ${PANDIR}/panoptes-utils/
RUN cd ${PANDIR}/panoptes-utils && \
    python setup.py develop && \
    # Get the CR2 testing file.
    wget -qO- $cr2_url > "${PANDIR}/panoptes-utils/tests/data/canon.cr2" && \
    # Download astrometry.net files
    python scripts/download-data.py \
        --wide-field --narrow-field \
        --folder "${astrometry_dir}" \
        --verbose

# Cleanup apt.
RUN apt-get autoremove --purge -y gcc pkg-config && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${PANDIR}/panoptes-utils

CMD ["/bin/bash"]
