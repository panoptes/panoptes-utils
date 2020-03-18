FROM python:3.8-slim-buster AS base-image
LABEL maintainer="developers@projectpanoptes.org"
LABEL website="https://projectpanoptes.org"

# Can override these from commandline.
ARG panuser=panoptes
ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"
ARG user_id=1000

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SOLVE_FIELD=/usr/bin/solve-field
ENV PANDIR $pan_dir
ENV PANUSER $panuser
ENV POCS $pocs_dir
ENV SHELL /bin/zsh
ENV ZSH_CUSTOM "/.oh-my-zsh/custom"

USER root

COPY ./docker/zshrc /etc/skel/panoptes-zshrc

# System dependencies.
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
    # Copy generated files to skeleton.
    cp -r /root/.oh-my-zsh /etc/skel && \
    # Append our custom additions to root and skeleton.
    cat /etc/skel/panoptes-zshrc >> /root/.zshrc && \
    cat /etc/skel/panoptes-zshrc >> /etc/skel/.zshrc && \
    # Astrometry folders.
    mkdir -p "/astrometry/data" && \
    echo "add_path /astrometry/data" >> /etc/astrometry.cfg && \
    # Create a panoptes group and change group ownership
    groupadd ${PANUSER} &&  \
    useradd --uid $user_id \
        --gid $user_id \
        --create-home \
        --non-unique \
        --shell /bin/zsh \
        --groups plugdev,dialout,users \
        --comment "PANOPTES User" \
        "${PANUSER}" && \
    # Create directories
    mkdir -p ${POCS} && \
    mkdir -p ${PANDIR}/logs && \
    mkdir -p ${PANDIR}/images && \
    mkdir -p ${PANDIR}/panoptes-utils && \
    # Change permissions on directories
    chown -R ${PANUSER}:${PANUSER} "${HOME}" && chmod -R 775 "${HOME}" && \
    chown -R ${PANUSER}:${PANUSER} "${PANDIR}" && chmod -R 775 "${PANDIR}" && \
    chown -R ${PANUSER}:${PANUSER} /astrometry && chmod -R 775 /astrometry

# Copy files as "panoptes" user.
WORKDIR ${PANDIR}/panoptes-utils
USER $PANUSER
# Note: can't make interpolation of $user_id work so hard-coded.
COPY --chown=1000:1000 . ${PANDIR}/panoptes-utils/

ENV PATH "/home/${PANUSER}/.local/bin:$PATH"

# Install module.
RUN cd ${PANDIR}/panoptes-utils && \
    # Install requirements.
    # First deal with pip and PyYAML - see https://github.com/pypa/pip/issues/5247.
    pip install --no-cache-dir --no-deps --ignore-installed pip PyYAML && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e . && \
    # Download astrometry.net files.
    python scripts/download-data.py \
        --wide-field --narrow-field \
        --folder "/astrometry/data" \
        --verbose && \
    # Create an SSH key
    ssh-keygen -q -t rsa -N "" -f "${HOME}/.ssh/id_rsa"

# Cleanup apt.
USER root
RUN apt-get autoremove --purge -y gcc pkg-config && \
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

# Back to regular user.
USER $PANUSER
WORKDIR ${PANDIR}/panoptes-utils

# Comes from base image - hard-coded for now ☹.
ENTRYPOINT ["/bin/sh", "/var/panoptes/panoptes-utils/docker/entrypoint.sh"]

CMD ["/bin/zsh"]
