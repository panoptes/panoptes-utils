ARG base_image=continuumio/miniconda3

FROM $base_image AS base-image
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SOLVE_FIELD=/usr/bin/solve-field
ENV PANDIR $pan_dir
ENV POCS $pocs_dir
ENV SHELL /bin/zsh
ENV ZSH_CUSTOM "/.oh-my-zsh/custom"

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
    echo "add_path /astrometry/data" >> /etc/astrometry.cfg

WORKDIR ${PANDIR}/panoptes-utils

# No ENTRYPOINT or CMD because this is used as a first stage
