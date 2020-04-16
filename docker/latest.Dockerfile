ARG base_image=python:3.8-slim-buster

FROM $base_image AS base-image
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

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

# For now we copy from local - can have bad effects if in wrong branch
COPY docker/zshrc /tmp

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gosu wget curl bzip2 ca-certificates zsh openssh-client nano \
        astrometry.net sextractor dcraw exiftool libcfitsio-dev libcfitsio-bin imagemagick \
        libfreetype6-dev libpng-dev libpq-dev fonts-lato \
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
    chown -R ${USERID}:${USERID} "/home/${panuser}" && \
    chown -R ${USERID}:${USERID} ${PANDIR} && \
    # Astrometry folders
    mkdir -p "${astrometry_dir}" && \
    chown -R ${USERID}:${USERID} ${astrometry_dir} && \
    echo "add_path ${astrometry_dir}" >> /etc/astrometry.cfg

USER $PANUSER

# Can't seem to get around the hard-coding
COPY --chown=panoptes:panoptes . ${PANDIR}/panoptes-utils/

RUN cd ${PANDIR}/panoptes-utils && \
    # First deal with pip and PyYAML - see https://github.com/pypa/pip/issues/5247
    pip install --no-cache-dir --no-deps --ignore-installed pip PyYAML && \
    # Install requirements
    pip install --no-cache-dir -r requirements.txt && \
    # Install module
    pip install --no-cache-dir -e . && \
    # Download astrometry.net files
    python scripts/download-data.py \
        --wide-field --narrow-field \
        --folder "${astrometry_dir}" \
        --verbose

USER root

# Cleanup apt.
RUN apt-get autoremove --purge -y gcc pkg-config && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${PANDIR}/panoptes-utils

# Comes from base image - hard-coded for now ☹.
ENTRYPOINT ["/bin/sh", "/var/panoptes/panoptes-utils/docker/entrypoint.sh"]

CMD ["/bin/zsh"]
