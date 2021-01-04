FROM busybox

ARG INDEX_START=4208
ARG INDEX_END=4219
ARG index_dir="/astrometry/data"
ENV INDEX_DIR $index_dir
ENV BASE_URL "http://broiler.astrometry.net/~dstn/4200/"

WORKDIR "${INDEX_DIR}"
RUN echo "Getting index files ${INDEX_START} - ${INDEX_END}" && \
    for i in $(seq ${INDEX_START} ${INDEX_END}); \
        do wget "${BASE_URL}/index-${i}.fits" -O "${INDEX_DIR}/index-${i}.fits"; \
    done
