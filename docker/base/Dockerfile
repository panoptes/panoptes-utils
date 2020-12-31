ARG IMAGE_URL=ubuntu:latest

FROM ${IMAGE_URL} AS base-image
LABEL description="Installs the panoptes-utils module from pip. \
Used as a production image, e.g. for running panoptes-network items."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash

ENV PANDIR $pan_dir
ENV POCS $pocs_dir
ENV PANLOG "$pan_dir/logs"

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        dcraw exiftool libcfitsio-dev libcfitsio-bin \
        libfreetype6-dev libpng-dev libjpeg-dev && \
    # Create PANOPTES directories.
    mkdir -p ${PANDIR} && \
    mkdir -p ${PANDIR}/logs && \
    mkdir -p ${PANDIR}/images && \
    mkdir -p ${PANDIR}/temp && \
    mkdir -p ${PANDIR}/panoptes-utils

# Install miniforge (conda-forge) as PANUSER
COPY ./resources/environment.yaml /tmp/
RUN mkdir -p "${PANDIR}/scripts/" && \
    wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh" \
        -O "${PANDIR}/scripts/install-miniforge.sh" && \
    /bin/sh "${PANDIR}/scripts/install-miniforge.sh" -b -f -p "${PANDIR}/conda" && \
    # Remove install file.
    rm "${PANDIR}/scripts/install-miniforge.sh" && \
    # Make sure to use conda for some of the larger modules.
    "${PANDIR}/conda/bin/conda" env update --file /tmp/environment.yaml && \
    # Initialize conda for the shells.
    "${PANDIR}/conda/bin/conda" init bash && \
    # Cleanup conda.
    "${PANDIR}/conda/bin/conda" clean -tipy

WORKDIR "${PANDIR}"
