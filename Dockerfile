FROM python:slim-buster
ARG DEBIAN_FRONTEND=noninteractive

ARG username=panoptes

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
      dcraw exiftool libcfitsio-bin astrometry.net \
      python3-scipy python3-matplotlib python3-numpy \
      python3-ruamel \
      && \
    # Add user.
    useradd -ms /bin/bash ${username} && \
    # Set up directories.
    chown -R ${username}:${username} /usr/share/astrometry && \
    # Cleanup
    apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

USER ${username}
ENV PATH=/home/${username}/.local/bin:$PATH
RUN pip3 install --no-cache -U pip && pip3 install --no-cache "panoptes-utils[images]"
ENTRYPOINT ["panoptes-utils"]
