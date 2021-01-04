FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash

ARG pan_dir=/var/panoptes
ENV PANDIR $pan_dir

ARG pip_extras="[config,images,testing,social]"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-pip wait-for-it \
        bzip2 ca-certificates git gcc pkg-config \
        libffi-dev libssl-dev \
        astrometry.net astrometry-data-2mass-08-19 \
        dcraw exiftool libcfitsio-dev libcfitsio-bin \
        libfreetype6-dev libpng-dev libjpeg-dev

WORKDIR "${PANDIR}/panoptes-utils"
COPY . .
RUN cd ${PANDIR}/panoptes-utils && \
    # Install module
    pip3 install -e ".${pip_extras}" && \
    # Cleanup
    apt-get autoremove --purge --yes \
        gcc pkg-config && \
    apt-get autoclean --yes && \
    apt-get --yes clean && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/bin/bash", "-ic"]
CMD [ "" ]
