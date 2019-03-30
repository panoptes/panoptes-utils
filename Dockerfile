# PANOPTES development container

FROM python:3-slim-stretch AS build-env
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

# Note that pocs-base has the default ubuntu environment, so
# we need to specify python3 so we don't get python2

# Use "bash" as replacement for "sh"
# Note: I don't think this is the preferred way to do this anymore
RUN rm /bin/sh && ln -s /bin/bash /bin/sh \
    && apt-get update \
    && apt-get --yes install \
        astrometry.net \
        libcfitsio-dev \
        python3-pip \
        wget \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p $POCS \
    && mkdir -p $PANLOG \
    && mkdir -p ${PANDIR}/astrometry/data \
    && echo "add_path /var/panoptes/astrometry/data" >> /etc/astrometry.cfg \
    && pip3 install -Ur requirements.txt \
    && python3 panoptes_utils/data.py \
    && pip3 install -e ".[google,social,testing,mongo]"

CMD ["python"]