ARG image_url=gcr.io/panoptes-exp/panoptes-base:latest

FROM ${image_url} AS base-image

ARG panuser=panoptes
ARG pan_dir=/var/panoptes
ARG conda_env_name="panoptes"
# Default install latest from pip.
ARG pip_install="panoptes-utils[testing,google]"

ENV PANUSER $panuser
ENV PANDIR $pan_dir

# Install module
USER ${PANUSER}
WORKDIR "${PANDIR}/panoptes-utils"
COPY . .
RUN "${PANDIR}/conda/envs/${conda_env_name}/bin/pip" install "${pip_install}" && \
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
ENTRYPOINT ["/bin/sh", "/var/panoptes/panoptes-utils/scripts/entrypoint.sh"]

CMD ["/usr/bin/zsh"]
