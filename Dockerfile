FROM python:3.12-slim-bookworm AS base

ARG DEBIAN_FRONTEND=noninteractive
ARG OUTPUT_BASE_DIR=/data
ENV OUTPUT_BASE_DIR=${OUTPUT_BASE_DIR}
WORKDIR /app
ARG OPENTOFU_VERSION=1.10.6
RUN apt-get update \
    && apt-get install --assume-yes --no-install-recommends \
        curl \
        git \
        gnupg \
        libpq-dev \
        software-properties-common \
        unzip \
    && curl -fsSL https://get.opentofu.org/install-opentofu.sh -o /tmp/install-opentofu.sh \
    && chmod +x /tmp/install-opentofu.sh \
    && /tmp/install-opentofu.sh --install-method standalone --opentofu-version "${OPENTOFU_VERSION}" \
    && rm /tmp/install-opentofu.sh \
    && rm -rf /var/lib/apt/lists/*
COPY ./requirements/common.txt requirements/common.txt
RUN python3 -m pip install --no-cache-dir --upgrade pip setuptools \
    && python3 -m pip install --no-cache-dir -r requirements/common.txt
COPY . .
RUN mkdir ${OUTPUT_BASE_DIR}
ENTRYPOINT [ "python", "/app/start.py" ]

FROM base AS local

COPY ./requirements/local.txt requirements/local.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
        make \
        openssh-client \
    && python3 -m pip install --no-cache-dir -r requirements/local.txt
RUN python3 -m pip install --no-cache-dir -r requirements/local.txt
