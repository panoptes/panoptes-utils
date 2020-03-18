ARG base_image=python:3.8-slim-buster

FROM $base_image AS base-image
LABEL maintainer="developers@projectpanoptes.org"

ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SOLVE_FIELD=/usr/bin/solve-field
ENV SHELL /bin/zsh
ENV ZSH_CUSTOM "/.oh-my-zsh/custom"

ENV PANDIR $pan_dir
ENV POCS $pocs_dir

# For now we copy from local - can have bad effects if in wrong branch
COPY . ${PANDIR}/panoptes-utils/

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gosu wget curl bzip2 ca-certificates zsh openssh-client nano \
        astrometry.net dcraw exiftool libcfitsio-dev libcfitsio-bin imagemagick \
        libfreetype6-dev libpng-dev libpq-dev fonts-lato \
        gcc git pkg-config sudo && \
    # Oh My ZSH. :)
    mkdir -p "${ZSH_CUSTOM}" && \
    chmod -R 755 "${ZSH_CUSTOM}" && \
    sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" && \
    git clone https://github.com/denysdovhan/spaceship-prompt.git "${ZSH_CUSTOM}/themes/spaceship-prompt" && \
    ln -s "${ZSH_CUSTOM}/themes/spaceship-prompt/spaceship.zsh-theme" "${ZSH_CUSTOM}/themes/spaceship.zsh-theme" && \
    cp -r /root/.oh-my-zsh /etc/skel && \
    cat "${PANDIR}/panoptes-utils/docker/zshrc" >> /root/.zshrc && \
    # Copy zshrc to /etc/skel for new users
    cat "${PANDIR}/panoptes-utils/docker/zshrc" >> /etc/skel/.zshrc && \
    # Astrometry folders
    mkdir -p "/astrometry/data" && \
    echo "add_path /astrometry/data" >> /etc/astrometry.cfg && \
    # Create a panoptes group and change group ownership
    groupadd panoptes && \
    # Create directories
    mkdir -p ${POCS} && \
    mkdir -p ${PANDIR}/logs && \
    mkdir -p ${PANDIR}/images && \
    mkdir -p ${PANDIR}/panoptes-utils && \
    # Install module
    cd ${PANDIR}/panoptes-utils && \
    # First deal with pip and PyYAML - see https://github.com/pypa/pip/issues/5247
    pip install --no-cache-dir --no-deps --ignore-installed pip PyYAML && \
    # Install requirements
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e . && \
    # Change permissions on directories
    chgrp -R panoptes /var/panoptes && chmod -R 775 /var/panoptes && \
    # Download astrometry.net files
    python scripts/download-data.py \
        --wide-field --narrow-field \
        --folder "/astrometry/data" \
        --verbose && \
    chgrp -R panoptes /astrometry && chmod -R 775 /astrometry && \
    # Cleanup apt.
    apt-get autoremove --purge -y gcc pkg-config && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${PANDIR}/panoptes-utils

# Comes from base image - hard-coded for now ☹.
ENTRYPOINT ["/bin/sh", "/var/panoptes/panoptes-utils/docker/entrypoint.sh"]

CMD ["/bin/zsh"]
