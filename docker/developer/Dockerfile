ARG image_url=gcr.io/panoptes-exp/panoptes-utils:develop
FROM ${image_url} AS base-image

LABEL description="Installs the panoptes-utils module with extra. \
development tools."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ARG panuser=panoptes
ARG userid=1000
ARG pan_dir=/var/panoptes
ARG conda_env_name="panoptes"

ENV USERID $userid
ENV PANUSER $panuser
ENV PANDIR $pan_dir
ENV CONDADIR "${PANDIR}/conda/envs/${conda_env_name}"

# Install module
USER "${PANUSER}"
WORKDIR "${PANDIR}/panoptes-utils"

# Can't seem to get around the hard-coding here.
COPY --chown=panoptes:panoptes . .
RUN echo "Installing developer modules" && \
    "${PANDIR}/conda/bin/conda" install --yes --name "${conda_env_name}" \
        jupyterlab \
        ipython \
        # Plotting
        bokeh \
        altair \
    && \
    # Cleanup
    sudo apt-get autoremove --purge --yes && \
    sudo apt-get autoclean --yes && \
    sudo apt-get --yes clean && \
    sudo rm -rf /var/lib/apt/lists/*

USER root
CMD ["${CONDADIR}/bin/ipython"]
