ARG IMAGE_URL=python:3.8-slim-buster

FROM ${IMAGE_URL} AS base-image
LABEL description="Installs the panoptes-utils module from pip. \
Used as a production image, e.g. for running panoptes-network items."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ARG panuser=panoptes
ARG userid=1000
ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"
ARG astrometry_dir="/astrometry/data"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/zsh
ENV ZSH_CUSTOM "/.oh-my-zsh/custom"

ENV USERID $userid
ENV PANDIR $pan_dir
ENV PANLOG "$pan_dir/logs"
ENV PANUSER $panuser
ENV POCS $pocs_dir
ENV PATH "/home/${PANUSER}/.local/bin:$PATH"
ENV SOLVE_FIELD /usr/bin/solve-field

COPY docker/zshrc /tmp
COPY ./scripts/download-data.py /tmp/download-data.py

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gosu wget curl bzip2 ca-certificates zsh openssh-client nano \
        astrometry.net sextractor dcraw exiftool libcfitsio-dev libcfitsio-bin imagemagick \
        libfreetype6-dev libpng-dev fonts-lato libsnappy-dev \
        gcc git pkg-config sudo && \
    # Oh My ZSH. :)
    mkdir -p "${ZSH_CUSTOM}" && \
    chmod -R 755 "${ZSH_CUSTOM}" && \
    sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" && \
    git clone https://github.com/denysdovhan/spaceship-prompt.git "${ZSH_CUSTOM}/themes/spaceship-prompt" && \
    ln -s "${ZSH_CUSTOM}/themes/spaceship-prompt/spaceship.zsh-theme" "${ZSH_CUSTOM}/themes/spaceship.zsh-theme" && \
    cp -r /root/.oh-my-zsh /etc/skel && \
    cat "/tmp/zshrc" >> /root/.zshrc && \
    # Copy zshrc to /etc/skel for new users
    cat "/tmp/zshrc" >> /etc/skel/.zshrc && \
    # Create directories
    mkdir -p ${POCS} && \
    mkdir -p ${PANDIR}/logs && \
    mkdir -p ${PANDIR}/images && \
    mkdir -p ${PANDIR}/panoptes-utils && \
    # Create $PANUSER
    useradd --shell /bin/zsh -u ${USERID} -o -c "PANOPTES User" -p panoptes -m -G plugdev,dialout $panuser && \
    # Create ssh-key for user
    mkdir -p /home/$panuser/.key && \
    ssh-keygen -q -t rsa -N "" -f "/home/${panuser}/.key/id_rsa" && \
    # Update permissions for current user.
    chown -R ${PANUSER}:${PANUSER} "/home/${panuser}" && \
    chown -R ${PANUSER}:${PANUSER} ${PANDIR} && \
    # Install module
    pip install "panoptes-utils[testing]" && \
    # astrometry.net folders
    mkdir -p "${astrometry_dir}" && \
    echo "add_path ${astrometry_dir}" >> /etc/astrometry.cfg && \
    # astrometry.net index files
    python /tmp/download-data.py \
        --wide-field --narrow-field \
        --folder "${astrometry_dir}" \
        --verbose && \
    chown -R ${PANUSER}:${PANUSER} ${astrometry_dir} && \
    chmod -R 777 ${astrometry_dir} && \
    # Cleanup
    apt-get autoremove --purge -y \
        autoconf \
        automake \
        autopoint \
        build-essential \
        gcc \
        gettext \
        libtool \
        pkg-config && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${PANDIR}/panoptes-utils

# Comes from base image - hard-coded for now ☹.
ENTRYPOINT ["/bin/sh", "/var/panoptes/panoptes-utils/docker/entrypoint.sh"]

CMD ["/bin/zsh"]
