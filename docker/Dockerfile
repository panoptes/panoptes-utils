ARG image_url=gcr.io/panoptes-exp/panoptes-base:latest

FROM ${image_url} AS base-image

ARG panuser=panoptes
ARG pan_dir=/var/panoptes
ARG conda_env_name="panoptes"
# Default install latest from pip.
ARG github_branch="${BRANCH_NAME:-master}"
ARG pip_extras="[testing,google,social]"
ARG pip_install="git+https://github.com/panoptes/panoptes-utils@${github_branch}#egg=panoptes-utils"

ENV PANUSER $panuser
ENV PANDIR $pan_dir

# Install module
USER ${PANUSER}
WORKDIR "${PANDIR}/panoptes-utils"

# Can't seem to get around the hard-coding here.
COPY --chown=panoptes:panoptes . .
RUN echo "Installing ${pip_install}" && \
    "${PANDIR}/conda/envs/${conda_env_name}/bin/pip" install -e "${pip_install}${pip_extras}" && \
    # Cleanup
    sudo apt-get autoremove --purge -y \
        autoconf \
        automake \
        autopoint \
        build-essential \
        gcc \
        gettext \
        libtool \
        pkg-config && \
    sudo apt-get autoremove --purge -y && \
    sudo apt-get -y clean && \
    sudo rm -rf /var/lib/apt/lists/* && \
    "${PANDIR}/conda/bin/conda" clean -tipsy

USER root
ENTRYPOINT ["/bin/sh", "/var/panoptes/panoptes-utils/docker/entrypoint.sh"]
CMD ["/usr/bin/zsh"]
