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
    curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get install -y --no-install-recommends \
        wget curl bzip2 ca-certificates nano neovim \
        gcc git pkg-config ncdu sudo nodejs && \
    echo "$PANUSER ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER $PANUSER

# Can't seem to get around the hard-coding
COPY --chown=panoptes:panoptes . ${PANDIR}/panoptes-utils/

RUN cd ${PANDIR}/panoptes-utils && \
    pip install --no-cache-dir -r dev-requirements.txt && \
    pip install --no-cache-dir -e . && \
    # Set some jupyterlab defaults
    mkdir -p /home/panoptes/.jupyter && \
    jupyter-lab --generate-config && \
    echo "c.JupyterApp.answer_yesBool = True" >> \
        "/home/panoptes/.jupyter/jupyter_notebook_config.py" && \
    echo "c.JupyterApp.open_browserBool = False" >> \
        "/home/panoptes/.jupyter/jupyter_notebook_config.py" && \
    echo "FileContentsManager.root_dirUnicode = '${PANDIR}'" >> \
        "/home/panoptes/.jupyter/jupyter_notebook_config.py" && \
    jupyter labextension install @pyviz/jupyterlab_pyviz \
                                jupyterlab-drawio \
                                @aquirdturtle/collapsible_headings \
                                @telamonian/theme-darcula

USER root

# Cleanup apt.
RUN apt-get autoremove --purge -y && \
    apt-get -y clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR ${PANDIR}

CMD ["/home/panoptes/.local/bin/jupyter-lab"]
