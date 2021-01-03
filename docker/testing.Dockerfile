FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash

ARG pan_dir=/var/panoptes
ENV PANDIR $pan_dir

ARG pip_extras="[config,images,testing,social]"
ARG astrometry_dir="/astrometry/data"

WORKDIR "${PANDIR}/panoptes-utils"
COPY ./resources/environment.yaml /tmp/
COPY . .
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-pip wait-for-it \
        bzip2 ca-certificates git gcc pkg-config \
        libffi-dev libssl-dev astrometry.net \
        dcraw exiftool libcfitsio-dev libcfitsio-bin \
        libfreetype6-dev libpng-dev libjpeg-dev && \
    # Download astrometry.net index files.
    mkdir -p "${astrometry_dir}" && \
    echo "add_path ${astrometry_dir}" >> /etc/astrometry.cfg && \
    cd ${PANDIR}/panoptes-utils && \
    # Install module
    pip3 install -e ".${pip_extras}" && \
    python3 scripts/download-data.py \
        --narrow-field \
        --folder "${astrometry_dir}" \
        --verbose || exit 0 && \
    # Cleanup
    apt-get autoremove --purge --yes \
        gcc pkg-config && \
    apt-get autoclean --yes && \
    apt-get --yes clean && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/bin/bash", "-ic"]
CMD [ "" ]
