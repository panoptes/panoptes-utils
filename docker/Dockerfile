ARG base_image=python:3.7-slim

FROM $base_image AS base-image
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG user=panoptes
ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"

ENV user $user
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash
ENV PANDIR $pan_dir
ENV POCS $pocs_dir
ENV PANUSER $user
ENV SOLVE_FIELD=/usr/bin/solve-field
ENV DEBIAN_FRONTEND=noninteractive
ENV ZSH_CUSTOM "/home/${user}/.oh-my-zsh/custom"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget curl bzip2 ca-certificates pkg-config zsh git fonts-lato nano \
        astrometry.net sextractor dcraw exiftool libcfitsio-dev libcfitsio-bin imagemagick \
        libcfitsio-dev libfreetype6-dev libpng-dev libpq-dev ack gcc && \
    # Create our user (use zsh by default)
    useradd -m -d "/home/${user}" "${user}" -s /bin/zsh && \
    export HOME="/home/${user}" && \
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
    cd "/home/${user}" && \
    wget https://sdk.cloud.google.com -O gsdk.sh && \
    bash gsdk.sh --disable-prompts && \
    echo ". /home/${user}/google-cloud-sdk/completion.zsh.inc" >> ~/.zshrc && \
    echo ". /home/${user}/google-cloud-sdk/path.zsh.inc" >> ~/.zshrc && \
    rm gsdk.sh && \
    echo "add_path /astrometry/data" >> /etc/astrometry.cfg && \
    # Cleanup apt.
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    # Change permissions and owners of directories
    chown -R "${user}" "/home/${user}" && \
    chown -R "${user}" "${PANDIR}" && \
    chown -R "${user}" /astrometry && \
    chmod -R 755 "/home/${user}"

WORKDIR ${PANDIR}

USER ${user}

# No ENTRYPOINT or CMD because this is use as a first stage
