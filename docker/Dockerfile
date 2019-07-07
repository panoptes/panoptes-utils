ARG base_image=python:3.7-slim

FROM $base_image AS base-image
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG user=root
ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"

ENV USER $user
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash
ENV PANDIR $pan_dir
ENV POCS $pocs_dir
ENV PANUSER $USER
ENV SOLVE_FIELD=/usr/bin/solve-field
ENV DEBIAN_FRONTEND=noninteractive
ENV ZSH_CUSTOM "/${USER}/.oh-my-zsh/custom"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget curl bzip2 ca-certificates pkg-config zsh git fonts-lato nano \
        astrometry.net sextractor dcraw exiftool libcfitsio-dev libcfitsio-bin imagemagick \
        libcfitsio-dev libfreetype6-dev libpng-dev libpq-dev ack gcc grc ncdu htop && \
    # Oh My ZSH. :)
    sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" && \
    git clone https://github.com/denysdovhan/spaceship-prompt.git "${ZSH_CUSTOM}/themes/spaceship-prompt" && \
    ln -s "${ZSH_CUSTOM}/themes/spaceship-prompt/spaceship.zsh-theme" "${ZSH_CUSTOM}/themes/spaceship.zsh-theme" && \
    # Create directories
    mkdir -p ${POCS} && \
    mkdir -p ${PANDIR}/logs && \
    mkdir -p ${PANDIR}/astrometry/data && \
    mkdir -p ${PANDIR}/images && \
    mkdir -p ${PANDIR}/panoptes-utils && \
    mkdir -p /astrometry/data && \
    # Google Cloud SDK
    cd "/${USER}" && \
    wget https://sdk.cloud.google.com -O gsdk.sh && \
    bash gsdk.sh --disable-prompts && \
    echo ". /${USER}/google-cloud-sdk/completion.zsh.inc" >> ~/.zshrc && \
    echo ". /${USER}/google-cloud-sdk/path.zsh.inc" >> ~/.zshrc && \
    rm gsdk.sh && \
    echo "add_path /astrometry/data" >> /etc/astrometry.cfg && \
    # Cleanup apt.
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Change permissions and owners of directories
    chown -R "${USER}" "/${USER}" && \
    chown -R "${USER}" "${PANDIR}" && \
    chown -R "${USER}" /astrometry && \
    chmod -R 755 "/${USER}"

WORKDIR ${PANDIR}/panoptes-utils

USER ${USER}

# No ENTRYPOINT or CMD because this is use as a first stage
