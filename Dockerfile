# Miniconda items taken from: https://hub.docker.com/r/continuumio/miniconda3/dockerfile
# Updated with "latest" miniconda script.

ARG base_image

FROM $base_image AS base-image
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG conda_url
ARG pan_dir=/var/panoptes

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash
ENV ENV /root/.bashrc
ENV PANDIR $pan_dir
ENV POCS ${PANDIR}/POCS
ENV PANUSER root
ENV SOLVE_FIELD=/usr/bin/solve-field
ENV DEBIAN_FRONTEND=noninteractive
# ENV conda_url $conda_url

WORKDIR ${PANDIR}/panoptes-utils/
COPY . ${PANDIR}/panoptes-utils/

# System packages
RUN apt-get update && \
    apt-get install -y \
        wget bzip2 ca-certificates pkg-config \
        astrometry.net dcraw exiftool \
        libcfitsio-dev libfreetype6-dev libpng-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Conda install
RUN wget --quiet ${conda_url} -O ~/conda.sh && \
    /bin/bash ~/conda.sh -b -p /opt/conda && \
    rm ~/conda.sh && \
    /opt/conda/bin/conda clean -tipsy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate" >> ~/.bashrc && \
    # End miniconda items
    mkdir -p $POCS \
    && mkdir -p ${PANDIR}/logs \
    && mkdir -p ${PANDIR}/astrometry/data \
    && mkdir -p ${PANDIR}/images \
    && echo "add_path /var/panoptes/astrometry/data" >> /etc/astrometry.cfg

# New RUN line so we don't keep rebuilding previous.
# Also installs pip requirements.txt
# Also installs panoptes-utils
RUN conda env create -f /var/panoptes/panoptes-utils/conda-environment.yaml \
    && conda activate panoptes-env \
    && echo "conda activate panoptes-env" >> ~/.bashrc \
    && cd ${PANDIR}/panoptes-utils \
    && python setup.py devel \
    # Download astrometry.net files 
    # TODO add cron job for IERS data download
    && python panoptes_utils/data.py

CMD ["python"]