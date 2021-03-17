ARG image_url=ubuntu
ARG image_tag=latest
FROM ${image_url}:${image_tag} AS pocs-utils

LABEL description="Installs the dependencies for panoptes-utils."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

ARG panuser=pocs-user
ARG userid=1000
ARG pip_install_extras="[config]"

ENV PANUSER $panuser
ENV USERID $userid
ENV PATH "/home/${PANUSER}/.local/bin:$PATH"

# Install system dependencies as root user.
RUN echo "Building from ${image_name}:${image_tag}" && \
    apt-get update && apt-get install --no-install-recommends --yes \
        bzip2 ca-certificates \
        wget gcc git pkg-config sudo less udev wait-for-it \
        dcraw exiftool \
        astrometry.net \
        libcfitsio-dev libcfitsio-bin \
        libfreetype6-dev libpng-dev libjpeg-dev libffi-dev && \
    useradd -u ${USERID} -o -c "Captain POCS" \
        -p panoptes -m -G plugdev,dialout,users,sudo ${PANUSER} && \
    # Allow sudo without password.
    echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    # Setup SSH so localhost works without password
    mkdir -p "/home/${panuser}/.ssh" && \
    echo "Host localhost\n\tStrictHostKeyChecking no\n" >> "/home/${panuser}/.ssh/config"

# Change to our app user.
USER "${userid}"

# Miniconda
WORKDIR /tmp
RUN echo "Installing conda via miniforge" && \
    sudo mkdir -p /conda && \
    sudo chown -R "${PANUSER}:${PANUSER}" /conda && \
    # Miniforge
    wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh" \
        -O install-miniforge.sh && \
    /bin/sh install-miniforge.sh -b -f -p /conda && \
    # Initialize conda for the shells.
    /conda/bin/conda init bash && \
    rm install-miniforge.sh

ARG app_dir=/panoptes-utils
ENV APP_DIR $app_dir

WORKDIR "${APP_DIR}"
COPY docker/environment.yaml .
COPY docker/docker-compose.yaml .
RUN /conda/bin/conda-env update -n base -f environment.yaml

RUN echo "Installing panoptes-utils module with ${pip_install_extras}" && \
    /conda/bin/pip install "panoptes-utils${pip_install_extras}" && \
    # Cleanup
    /conda/bin/pip cache purge && \
    /conda/bin/conda clean -tipy && \
    sudo apt-get autoremove --purge --yes && \
    sudo apt-get autoclean --yes && \
    sudo apt-get --yes clean && \
    sudo rm -rf /var/lib/apt/lists/*

# We are still the PANUSER.
ENTRYPOINT [ "/usr/bin/env", "bash", "-ic" ]
CMD [ "panoptes-config-server", "--help" ]
