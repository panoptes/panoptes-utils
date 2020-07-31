ARG IMAGE_URL=gcr.io/panoptes-exp/panoptes-base:latest

FROM ${IMAGE_URL} AS base-image

ARG panuser=panoptes
ARG pan_dir=/var/panoptes
ARG conda_env_name="panoptes"

ENV PANUSER $panuser
ENV PANDIR $pan_dir

# Install module locally. Note that there must be a .git folder (e.g. a clone or zip).
USER ${PANUSER}
COPY . "${PANDIR}/panoptes-utils"
RUN cd "${PANDIR}/panoptes-utils" && \
    "${PANDIR}/conda/envs/${conda_env_name}/bin/pip" install ".[testing,google]" && \
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
WORKDIR "${PANDIR}/panoptes-utils"
CMD ["/bin/zsh"]
