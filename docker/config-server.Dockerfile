FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

ARG pan_dir=/var/panoptes
ENV PANDIR $pan_dir

RUN apt-get update && \
    apt-get install -y --no-install-recommends git \
        python3-pip \
        python3-astropy \
        python3-gevent \
        python3-numpy

WORKDIR "/var/panoptes/"
COPY . "${pan_dir}/panoptes-utils/"
RUN cd "${pan_dir}/panoptes-utils" && \
    pip3 install -e ".[config]" && \
    # Cleanup
    apt-get autoremove --purge --yes \
         git gcc pkg-config && \
    apt-get autoclean --yes && \
    apt-get --yes clean && \
    rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/bin/bash", "-c"]
CMD [ "panoptes-config-server --verbose run" ]
