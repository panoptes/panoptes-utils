FROM debian:buster-slim
ARG DEBIAN_FRONTEND=noninteractive

ARG username=panoptes

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
      wget ca-certificates bzip2 \
      dcraw exiftool libcfitsio-bin astrometry.net \
      python3-pip python3-scipy python3-matplotlib python3-numpy \
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
RUN python3 -m pip install --no-cache -U pip && python3 -m pip install --no-cache "panoptes-utils[images]"
ENTRYPOINT ["panoptes-utils"]
