FROM condaforge/miniforge3:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash

ARG pip_extras="[config,images,testing,social]"

WORKDIR /tmp
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wait-for-it \
        bzip2 ca-certificates git gcc pkg-config \
        libffi-dev libssl-dev \
        astrometry.net astrometry-data-2mass-08-19 \
        dcraw exiftool libcfitsio-dev libcfitsio-bin \
        libfreetype6-dev libpng-dev libjpeg-dev libffi-dev

COPY docker/environment.yaml .
RUN conda env update -n base -f environment.yaml

WORKDIR /app
COPY . .
RUN pip install -e ".${pip_extras}" && \
    # Cleanup
    apt-get autoremove --purge --yes \
        gcc pkg-config git && \
    apt-get autoclean --yes && \
    apt-get --yes clean && \
    rm -rf /var/lib/apt/lists/*

CMD [ "/opt/conda/bin/pytest" ]
