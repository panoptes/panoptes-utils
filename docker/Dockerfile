ARG image_url=ubuntu:latest
FROM ${image_url} AS base-image

LABEL description="Installs the panoptes-utils module."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash

ARG pan_dir=/var/panoptes
ENV PANDIR $pan_dir

ARG pip_extras="[testing,social]"
ARG astrometry_dir="/astrometry/data"

USER root
COPY ./resources/environment.yaml /tmp/
COPY ./scripts/download-data.py /tmp/download-data.py
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget bzip2 ca-certificates wait-for-it git gcc pkg-config \
        libffi-dev libssl-dev astrometry.net \
        dcraw exiftool libcfitsio-dev libcfitsio-bin \
        libfreetype6-dev libpng-dev libjpeg-dev && \
    # Create PANOPTES directories.
    mkdir -p ${PANDIR}/panoptes-utils && \
    # Install miniforge.
    wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh" \
        -O "/tmp/install-miniforge.sh" && \
    /bin/sh "/tmp/install-miniforge.sh" -b -f -p "${PANDIR}/conda" && \
    # Make sure to use conda for some of the larger modules.
    "${PANDIR}/conda/bin/conda" env update --file /tmp/environment.yaml && \
    # Initialize conda for the shells.
    "${PANDIR}/conda/bin/conda" init bash && \
    # Download astrometry.net index files.
    mkdir -p "${astrometry_dir}" && \
    echo "add_path ${astrometry_dir}" >> /etc/astrometry.cfg && \
    "${PANDIR}/conda/bin/python" /tmp/download-data.py \
        --wide-field --narrow-field \
        --folder "${astrometry_dir}" \
        --verbose || exit 0

# Install module
WORKDIR "${PANDIR}/panoptes-utils"
COPY . .
RUN echo "Installing editable module with ${pip_extras}" && \
    "${PANDIR}/conda/bin/pip" install -e ".${pip_extras}" && \
    # Cleanup
    apt-get autoremove --purge --yes \
        gcc pkg-config && \
    apt-get autoclean --yes && \
    apt-get --yes clean && \
    rm -rf /var/lib/apt/lists/* && \
    "${PANDIR}/conda/bin/conda" clean -tipy

ENTRYPOINT ["/bin/bash", "-ic"]
CMD [ "" ]
