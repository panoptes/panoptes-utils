# Miniconda items taken from: https://hub.docker.com/r/continuumio/miniconda3/dockerfile
# Updated with "latest" miniconda script.

ARG base_image=continuumio/miniconda3

FROM $base_image AS base-image
MAINTAINER Developers for PANOPTES project<https://github.com/panoptes/POCS>

ARG pan_dir=/var/panoptes

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV SHELL /bin/bash
ENV ENV /root/.bashrc
ENV PANDIR $pan_dir
ENV POCS ${PANDIR}/POCS
ENV PANUSER root
ENV SOLVE_FIELD=/usr/bin/solve-field
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR ${PANDIR}/panoptes-utils/
COPY . ${PANDIR}/panoptes-utils/

# System packages
RUN mkdir -p $POCS && \
    mkdir -p ${PANDIR}/logs && \
    mkdir -p ${PANDIR}/astrometry/data && \
    mkdir -p ${PANDIR}/images && \
    apt-get update && \
    apt-get install -y \
        wget bzip2 ca-certificates pkg-config zsh git \
        astrometry.net dcraw exiftool \
        libcfitsio-dev libfreetype6-dev libpng-dev libpq-dev && \
    # Oh My ZSH. :)
    chsh -s /bin/zsh && \
    sh -c "$(wget https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "add_path /var/panoptes/astrometry/data" >> /etc/astrometry.cfg

FROM base-image AS conda-install

# Conda install
RUN /opt/conda/bin/conda env create -f conda-environment.yaml && \
    /opt/conda/bin/conda clean --all --yes && \
    /opt/conda/bin/conda clean -tipsy && \
    echo "conda activate panoptes-env" >> ~/.bashrc && \
    echo "conda activate panoptes-env" >> ~/.zshrc && \
    # End miniconda items
    # Download astrometry.net files 
    # TODO add cron job for IERS data download
    /opt/conda/envs/panoptes-env/bin/python panoptes_utils/data.py --wide-field --narrow-field

CMD ["/bin/zsh"]
