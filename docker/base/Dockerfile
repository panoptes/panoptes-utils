ARG IMAGE_URL=ubuntu:latest

FROM ${IMAGE_URL} AS base-image
LABEL description="Installs the panoptes-utils module from pip. \
Used as a production image, e.g. for running panoptes-network items."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ARG panuser=panoptes
ARG pan_user_fullname="PANOPTES User"
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

COPY ./resources/docker/zshrc /tmp
COPY ./resources/docker/install-ohmyzsh.sh /tmp
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gosu wget curl bzip2 ca-certificates zsh openssh-client nano \
        astrometry.net source-extractor dcraw exiftool libcfitsio-dev libcfitsio-bin \
        libfreetype6-dev libpng-dev libjpeg-dev \
        libffi-dev libssl-dev \
        gcc git pkg-config sudo && \
    # All our shells are belong to Oh My ZSH w/ Spaceship prompt. :)
    echo "Install oh-my-zsh" && \
    mkdir -p "${ZSH_CUSTOM}" && \
    chmod -R 755 "${ZSH_CUSTOM}" && \
    sh /tmp/install-ohmyzsh.sh --unattended && \
    # ZSH theme.
    git clone --single-branch --quiet https://github.com/denysdovhan/spaceship-prompt.git "${ZSH_CUSTOM}/themes/spaceship-prompt" && \
    ln -s "${ZSH_CUSTOM}/themes/spaceship-prompt/spaceship.zsh-theme" "${ZSH_CUSTOM}/themes/spaceship.zsh-theme" && \
    # ZSH auto-suggestion plugin.
    git clone --single-branch --quiet https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM}/plugins/zsh-autosuggestions && \
    # Copy zshrc for root user.
    cat "/tmp/zshrc" >> /root/.zshrc && \
    # Copy generated oh-my-zsh for new users.
    cp -r /root/.oh-my-zsh /etc/skel/ && \
    # Copy zshrc to /etc/skel for new users.
    cat "/tmp/zshrc" >> /etc/skel/.zshrc && \
    # Create $PANUSER.
    echo "Creating new user ${USERID} ${PANUSER} '${pan_user_fullname}'" && \
    useradd --shell /bin/zsh -u ${USERID} -o -c "${pan_user_fullname}" \
        -p panoptes -m -G plugdev,dialout,users,sudo ${PANUSER} && \
    # Allow sudo without password.
    echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    # Create ssh-key for user.
    mkdir -p /home/${PANUSER}/.ssh && \
    ssh-keygen -q -t rsa -N "" -f "/home/${PANUSER}/.ssh/id_rsa" && \
    # astrometry.net folders.
    mkdir -p "${astrometry_dir}" && \
    echo "add_path ${astrometry_dir}" >> /etc/astrometry.cfg && \
    chown -R ${PANUSER}:${PANUSER} ${astrometry_dir} && \
    chmod -R 777 ${astrometry_dir} && \
    # Create PANOPTES directories.
    mkdir -p ${PANDIR} && \
    mkdir -p ${PANDIR}/logs && \
    mkdir -p ${PANDIR}/images && \
    mkdir -p ${PANDIR}/temp && \
    mkdir -p ${PANDIR}/.key && \
    mkdir -p ${PANDIR}/panoptes-utils && \
    # Update permissions for current user (root user created ssh).
    chown -R ${PANUSER}:${PANUSER} "/home/${PANUSER}" && \
    chown -R ${PANUSER}:${PANUSER} ${PANDIR}

# Install miniforge (conda-forge) as PANUSER
USER "${PANUSER}"
COPY --chown=panoptes:panoptes ./scripts/download-data.py "${PANDIR}/scripts/download-data.py"
COPY --chown=panoptes:panoptes ./resources/environment.yaml /tmp/
RUN mkdir -p "${PANDIR}/scripts/" && \
    wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh" \
        -O "${PANDIR}/scripts/install-miniforge.sh" && \
    /bin/sh "${PANDIR}/scripts/install-miniforge.sh" -b -f -p "${PANDIR}/conda" && \
    # Remove install file.
    rm "${PANDIR}/scripts/install-miniforge.sh" && \
    # Make sure to use conda for some of the larger modules.
    "${PANDIR}/conda/bin/conda" env update --file /tmp/environment.yaml && \
    # Initialize conda for the shells.
    "${PANDIR}/conda/bin/conda" init bash zsh && \
    printf "\necho PANOPTES utils activated!\n" >> "${HOME}/.zshrc" && \
    # Download index files.
    "${PANDIR}/conda/bin/python" "${PANDIR}/scripts/download-data.py" \
        --wide-field --narrow-field \
        --folder "${astrometry_dir}" \
        --verbose || exit 0 && \
    # Cleanup conda.
    "${PANDIR}/conda/bin/conda" clean -tipy

USER root
WORKDIR "${PANDIR}"
