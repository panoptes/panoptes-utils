ARG IMAGE_URL=ubuntu:latest

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
ARG cr2_url="https://storage.googleapis.com/panoptes-resources/test-data/canon.cr2"
ARG conda_env_name="panoptes"
ARG pan_user_fullname="PANOPTES User"

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

COPY ./docker/zshrc /tmp
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gosu wget curl bzip2 ca-certificates zsh openssh-client nano \
        astrometry.net sextractor dcraw exiftool libcfitsio-dev libcfitsio-bin imagemagick \
        libfreetype6-dev libpng-dev fonts-lato libsnappy-dev libjpeg-dev \
        libffi-dev libssl-dev \
        gcc git pkg-config sudo && \
    # All our shells are belong to Oh My ZSH w/ Spaceship prompt. :)
    mkdir -p "${ZSH_CUSTOM}" && \
    chmod -R 755 "${ZSH_CUSTOM}" && \
    sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" && \
    git clone --single-branch --quiet https://github.com/denysdovhan/spaceship-prompt.git "${ZSH_CUSTOM}/themes/spaceship-prompt" && \
    ln -s "${ZSH_CUSTOM}/themes/spaceship-prompt/spaceship.zsh-theme" "${ZSH_CUSTOM}/themes/spaceship.zsh-theme" && \
    cp -r /root/.oh-my-zsh /etc/skel && \
    cat "/tmp/zshrc" >> /root/.zshrc && \
    cat "/tmp/zshrc" >> /etc/skel/.zshrc && \

    # Create $PANUSER.
    useradd --shell /bin/zsh -u ${USERID} -o -c "${pan_user_fullname}" \
        -p panoptes -m -G plugdev,dialout,users,sudo ${PANUSER} && \

    # Allow sudo without password.
    echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers && \

    # Create ssh-key for user.
    mkdir -p /home/${PANUSER}/.key && \
    ssh-keygen -q -t rsa -N "" -f "/home/${PANUSER}/.key/id_rsa" && \

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
COPY --chown="${PANUSER}:${PANUSER}" ./scripts/download-data.py /tmp/download-data.py
RUN wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-$(uname -m).sh" \
        -O "${PANDIR}/install-miniforge.sh" && \
    /bin/sh "${PANDIR}/install-miniforge.sh" -b -f -p "${PANDIR}/conda" && \
    "${PANDIR}/conda/bin/conda" create -y -n "${conda_env_name}" python=3.8 \
        astroplan \
        astropy \
        click \
        loguru \
        matplotlib \
        numpy \
        pandas \
        scipy && \
    "${PANDIR}/conda/bin/conda" init zsh && \
    # Activate the environment by default.
    printf "\nconda activate ${conda_env_name}\n" >> "${HOME}/.zshrc" && \
    # Download astrometry.net index files.
    "${PANDIR}/conda/envs/${conda_env_name}/bin/python" /tmp/download-data.py \
        --wide-field --narrow-field \
        --folder "${astrometry_dir}" \
        --verbose

USER root
WORKDIR "${PANDIR}"

# Hard to avoid these hard-coded names for some reason.
COPY docker/entrypoint.sh /var/panoptes/scripts/docker-entrypoint.sh
ENTRYPOINT ["/bin/sh", "/var/panoptes/scripts/docker-entrypoint.sh"]

CMD ["/bin/zsh"]
