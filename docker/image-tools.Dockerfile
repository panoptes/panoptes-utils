FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

ARG pan_dir=/var/panoptes
ENV PANDIR $pan_dir

ARG astrometry_dir="/astrometry/data"

COPY ./scripts/download-data.py /tmp/download-data.py
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3-click \
        python3-matplotlib \
        python3-numpy \
        python3-photutils \
        python3-pil \
        python3-pip \
        python3-scipy \
        git libffi-dev astrometry.net \
        dcraw exiftool libcfitsio-dev libcfitsio-bin \
        libfreetype6-dev libpng-dev libjpeg-dev && \
    # Download astrometry.net index files.
    pip3 install astropy astroplan loguru && \
    mkdir -p "${astrometry_dir}" && \
    echo "add_path ${astrometry_dir}" >> /etc/astrometry.cfg && \
    python3 /tmp/download-data.py \
        --wide-field --narrow-field \
        --folder "${astrometry_dir}" \
        --verbose || exit 0

# Install module
WORKDIR "${PANDIR}/panoptes-utils"
COPY . .
RUN cd "${pan_dir}/panoptes-utils" && \
    pip3 install -e ".[images]" && \
    # Cleanup
    apt-get autoremove --purge --yes \
         git gcc pkg-config && \
    apt-get autoclean --yes && \
    apt-get --yes clean && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/bin/bash", "-ic"]
CMD [ "echo Make cli here." ]