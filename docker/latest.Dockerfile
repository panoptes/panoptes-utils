ARG IMAGE_URL=gcr.io/panoptes-exp/panoptes-base:latest

FROM ${IMAGE_URL} AS base-image

ARG panuser=panoptes
ARG pan_dir=/var/panoptes

ENV PANUSER $panuser
ENV PANDIR $pan_dir

# Install module
USER ${PANUSER}
RUN "${PANDIR}/conda/envs/${conda_env_name}/bin/pip" install -U "panoptes-utils[testing,google]" && \
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
    rm -rf /var/lib/apt/lists/* && \
    "${PANDIR}/conda/bin/conda" clean -tipsy

WORKDIR ${PANDIR}/panoptes-utils

CMD ["/bin/zsh"]
