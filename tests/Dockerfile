ARG image_url=panoptes-utils
ARG image_tag=latest
FROM ${image_url}:${image_tag}

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash
ENV PYTHONUNBUFFERED 1

RUN sudo apt-get update && sudo apt-get install -y --no-install-recommends astrometry-data-tycho2 && \
    # Cleanup
    sudo apt-get autoremove --purge --yes gcc pkg-config git && \
    sudo apt-get autoclean --yes && \
    sudo apt-get --yes clean && \
    sudo rm -rf /var/lib/apt/lists/*

CMD [ "/opt/conda/bin/pytest" ]
