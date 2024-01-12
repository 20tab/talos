FROM python:3.12-slim-bookworm AS base

ARG DEBIAN_FRONTEND=noninteractive
ARG OUTPUT_BASE_DIR=/data
ENV OUTPUT_BASE_DIR=${OUTPUT_BASE_DIR}
WORKDIR /app
COPY ./requirements/common.txt requirements/common.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        git \
        gnupg \
        libpq-dev \
        software-properties-common \
    && curl https://apt.releases.hashicorp.com/gpg | gpg --dearmor > /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    && gpg --no-default-keyring --keyring /usr/share/keyrings/hashicorp-archive-keyring.gpg --fingerprint \
    && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list \
    && apt-get update \
    && apt-get install --assume-yes --no-install-recommends \
        terraform \
    && python3 -m pip install --no-cache-dir --upgrade pip setuptools \
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
