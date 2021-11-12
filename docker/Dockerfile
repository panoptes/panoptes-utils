ARG image_url=mambaorg/micromamba
ARG image_tag=latest
FROM ${image_url}:${image_tag} AS panoptes-utils-base

LABEL description="Installs the dependencies for panoptes-utils."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED 1

ARG panuser=pocs-user
ARG userid=1000

ENV PANUSER $panuser
ENV USERID $userid
ENV PATH "/home/${PANUSER}/.local/bin:$PATH"

# Install system dependencies as root user.
USER root
RUN echo "Building from ${image_url}:${image_tag}" && \
    apt-get update && apt-get install --no-install-recommends --yes \
        bzip2 ca-certificates \
        wget gcc pkg-config sudo less udev wait-for-it \
        dcraw exiftool \
        nano neovim ncdu \
        astrometry.net \
        libcfitsio-dev libcfitsio-bin \
        libfreetype6-dev libpng-dev libjpeg-dev libffi-dev && \
    apt-get autoremove --purge --yes && \
    apt-get autoclean --yes && \
    apt-get --yes clean && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -u ${USERID} -o -c "Captain POCS" \
        -p panoptes -m -G plugdev,dialout,users,sudo ${PANUSER} && \
    # Allow sudo without password.
    echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \
    # Setup SSH so localhost works without password
    mkdir -p "/home/${panuser}/.ssh" && \
    echo "Host localhost\n\tStrictHostKeyChecking no\n" >> "/home/${panuser}/.ssh/config"

FROM panoptes-utils-base AS panoptes-utils-conda

USER "${PANUSER}"
COPY docker/environment.yaml /tmp/environment.yaml
RUN echo "Updating python environment." && \
    micromamba install -y -n base -f /tmp/environment.yaml && \
    micromamba clean --all --yes

FROM panoptes-utils-conda AS panoptes-utils

ARG app_dir=/panoptes-utils
ENV APP_DIR $app_dir

WORKDIR "${APP_DIR}"
USER "${USERID}"

ARG pip_install_name="panoptes-utils"
ARG pip_install_extras=""

COPY docker/docker-compose.yaml .
RUN echo "Installing panoptes-utils module with ${pip_install_extras}" && \
    pip install "${pip_install_name}${pip_install_extras}" && \
    # Cleanup
    pip cache purge

# We are still the PANUSER.
ENTRYPOINT [ "/usr/bin/env", "bash", "-ic" ]
CMD [ "panoptes-config-server", "--help" ]
