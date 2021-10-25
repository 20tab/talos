FROM python:3.9-slim-bullseye AS base

ARG DEBIAN_FRONTEND=noninteractive
ARG OUTPUT_BASE_DIR=/data
ENV OUTPUT_BASE_DIR=${OUTPUT_BASE_DIR}
WORKDIR /app
COPY --chown=$APPUSER ./requirements/common.txt requirements/common.txt
RUN python3 -m pip install --no-cache-dir -r requirements/common.txt
COPY . .
RUN mkdir ${OUTPUT_BASE_DIR}
ENTRYPOINT [ "/app/bootstrap.py" ]


FROM base AS remote

COPY --chown=$APPUSER ./requirements/remote.txt requirements/remote.txt
RUN python3 -m pip install --no-cache-dir -r requirements/remote.txt


FROM base AS local

COPY ./requirements/local.txt requirements/local.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        make \
        openssh-client \
    && python3 -m pip install --no-cache-dir -r requirements/local.txt
RUN python3 -m pip install --no-cache-dir -r requirements/local.txt
