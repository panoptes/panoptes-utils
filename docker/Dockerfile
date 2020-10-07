ARG image_url=gcr.io/panoptes-exp/panoptes-base:latest
FROM ${image_url} AS base-image

LABEL description="Installs the panoptes-utils module from GitHub. \
Used as the base image for most PANOPTES services."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ARG panuser=panoptes
ARG userid=1000
ARG pan_dir=/var/panoptes

ARG pip_extras="[testing,social]"

ENV USERID $userid
ENV PANUSER $panuser
ENV PANDIR $pan_dir

# Install module
USER "${PANUSER}"
WORKDIR "${PANDIR}/panoptes-utils"

# Can't seem to get around the hard-coding here.
COPY --chown=panoptes:panoptes . .
RUN echo "Installing editable module with ${pip_extras}" && \
    "${PANDIR}/conda/bin/pip" install -e ".${pip_extras}" && \
    # Cleanup
    sudo apt-get autoremove --purge --yes && \
    sudo apt-get autoclean --yes && \
    sudo apt-get --yes clean && \
    sudo rm -rf /var/lib/apt/lists/* && \
    "${PANDIR}/conda/bin/conda" clean -tipy

USER root
ENTRYPOINT ["/bin/sh", "/var/panoptes/panoptes-utils/resources/docker/entrypoint.sh"]
CMD ["/usr/bin/zsh"]
