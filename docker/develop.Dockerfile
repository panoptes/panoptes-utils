ARG IMAGE_URL=gcr.io/panoptes-exp/panoptes-utils:latest

FROM ${IMAGE_URL} AS base-image
LABEL description="Installs the panoptes-utils module from pip. \
Used as a production image, e.g. for testing."
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"
ARG cr2_url="https://storage.googleapis.com/panoptes-resources/test-data/canon.cr2"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/zsh

ARG userid=1000

ENV USERID $userid
ENV PANDIR $pan_dir
ENV PANLOG "$pan_dir/logs"
ENV PANUSER panoptes
ENV POCS $pocs_dir
ENV SOLVE_FIELD /usr/bin/solve-field

# Install module
USER ${PANUSER}
COPY --chown=panoptes:panoptes . "${PANDIR}/panoptes-utils/"
RUN wget -qO- $cr2_url > "${PANDIR}/panoptes-utils/tests/data/canon.cr2" && \
    cd "${PANDIR}/panoptes-utils" && \
    pip install -e ".[testing]"

# Cleanup apt.
USER root
RUN apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/* && \
    chown -R "${PANUSER}:${PANUSER}" "${PANDIR}" && \
    chmod -R 777 /astrometry

WORKDIR ${PANDIR}/panoptes-utils

CMD ["/bin/zsh"]
