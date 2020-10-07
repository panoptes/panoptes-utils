ARG image_url=gcr.io/panoptes-exp/panoptes-utils:develop
FROM ${image_url} AS base-image

LABEL description="Installs the panoptes-utils module with extra. \
development tools."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ARG panuser=panoptes
ARG userid=1000
ARG pan_dir=/var/panoptes

ENV USERID $userid
ENV PANUSER $panuser
ENV PANDIR $pan_dir

# Install module
USER "${PANUSER}"
WORKDIR "${PANDIR}/panoptes-utils"

# Can't seem to get around the hard-coding here.
COPY --chown=panoptes:panoptes . .
RUN echo "Installing developer modules" && \
    "${PANDIR}/conda/bin/conda" install --yes --name base \
        jupyterlab \
        ipython \
        pyarrow \
        # Plotting
        altair \
        bokeh \
        seaborn \
    && \
    # Cleanup
    sudo apt-get autoremove --purge --yes && \
    sudo apt-get autoclean --yes && \
    sudo apt-get --yes clean && \
    sudo rm -rf /var/lib/apt/lists/*

USER root
CMD ["${PANDIR}/conda/bin/ipython"]
