# PANOPTES development container
ARG PYARCH=x86_64

FROM multiarch/ubuntu-core:${PYARCH}-bionic AS build-env
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG pan_dir=/var/panoptes

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV ENV /root/.bashrc
ENV SHELL /bin/bash
ENV PANDIR $pan_dir
ENV PANLOG $PANDIR/logs 
ENV POCS $PANDIR/POCS  
ENV PANUSER root
ENV SOLVE_FIELD=/usr/bin/solve-field
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR ${PANDIR}/panoptes-utils/
COPY . ${PANDIR}/panoptes-utils/

RUN apt-get update \
    && apt-get --yes install \
        astrometry.net \
        dcraw \
        exiftool \
        libcfitsio-dev \
        libfreetype6-dev \
        libpng-dev \
        pkg-config \
        python3-pip \
        wget \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p $POCS \
    && mkdir -p $PANLOG \
    && mkdir -p ${PANDIR}/astrometry/data \
    && echo "add_path /var/panoptes/astrometry/data" >> /etc/astrometry.cfg \
    && pip3 install --no-cache-dir -r requirements.txt \
    && python3 panoptes_utils/data.py \
    && pip3 install -e ".[google,social,testing,mongo]"

CMD ["python3"]