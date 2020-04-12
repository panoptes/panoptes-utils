ARG base_image=gcr.io/panoptes-exp/panoptes-utils:latest

FROM $base_image AS base-image
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG panuser=panoptes
ARG userid=1000
ARG pan_dir=/var/panoptes
ARG pocs_dir="${pan_dir}/POCS"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/zsh

ENV USERID $userid
ENV PANDIR $pan_dir
ENV PANLOG "$pan_dir/logs"
ENV PANUSER $panuser
ENV POCS $pocs_dir
ENV PATH "/home/${PANUSER}/.local/bin:$PATH"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget curl bzip2 ca-certificates nano neovim \
        gcc git pkg-config ncdu

USER $PANUSER

# Can't seem to get around the hard-coding
COPY --chown=panoptes:panoptes . ${PANDIR}/panoptes-utils/

RUN cd ${PANDIR}/panoptes-utils && \
    pip install --no-cache-dir -r dev-requirements.txt && \
    pip install --no-cache-dir -e .

USER root

# Cleanup apt.
RUN apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${PANDIR}

CMD ["/home/panoptes/.local/bin/jupyter-lab", "--no-browser", "-y"]
