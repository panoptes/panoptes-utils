FROM debian:11-slim AS panoptes-utils-base
LABEL description="Base image tools for PANOPTES"
LABEL maintainers="developers@projectpanoptes.org"
LABEL repo="github.com/panoptes/panoptes-utils"

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PYTHONUNBUFFERED True

# Install system packages.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        wget sudo git \
        astrometry.net source-extractor dcraw exiftool \
        libcfitsio-dev libcfitsio-bin \
        libpng-dev libjpeg-dev \
        libfreetype6-dev \
        libffi-dev && \
    # Cleanup
    apt-get autoclean --yes && \
    apt-get --yes clean && \
    rm -rf /var/lib/apt/lists/*

ADD http://data.astrometry.net/4100/index-4108.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4110.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4111.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4112.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4113.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4114.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4115.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4116.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4117.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4118.fits /usr/share/astrometry
ADD http://data.astrometry.net/4100/index-4119.fits /usr/share/astrometry
