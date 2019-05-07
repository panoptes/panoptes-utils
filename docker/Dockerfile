# Miniconda items taken from: https://hub.docker.com/r/continuumio/miniconda3/dockerfile
# Updated with "latest" miniconda script.

ARG base_image=continuumio/miniconda3

FROM $base_image AS base-image
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG pan_dir=/var/panoptes
ARG pocs_dir=${pan_dir}/POCS

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash
ENV ENV /root/.bashrc
ENV PANDIR $pan_dir
ENV POCS $pocs_dir
ENV PANUSER root
ENV SOLVE_FIELD=/usr/bin/solve-field
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR ${PANDIR}

# System packages
RUN mkdir -p ${POCS} && \
    mkdir -p ${PANDIR}/logs && \
    mkdir -p ${PANDIR}/astrometry/data && \
    mkdir -p ${PANDIR}/images && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        wget bzip2 ca-certificates pkg-config zsh git fonts-lato \
        astrometry.net dcraw exiftool libcfitsio-dev libcfitsio-bin \
        libcfitsio-dev libfreetype6-dev libpng-dev libpq-dev && \
    # Oh My ZSH. :)
    chsh -s /bin/zsh && \
    sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" && \
    # Cleanup apt.
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # We will download index files later but setup config now.
    echo "add_path ${PANDIR}/astrometry/data" >> /etc/astrometry.cfg
