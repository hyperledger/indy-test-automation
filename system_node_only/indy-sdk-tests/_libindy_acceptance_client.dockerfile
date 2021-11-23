FROM ubuntu:16.04

# generally useful packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        apt-transport-https \
        software-properties-common \
        curl \
        wget \
        ssh \
        vim \
        git \
    && rm -rf /var/lib/apt/lists/*

# java
RUN apt-get update && apt-get install -y \
        openjdk-8-jdk \
        maven

ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64

# python
RUN apt-get update && apt-get install -y \
        python3.5 \
        python3-pip \
        python-setuptools \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install -U \
        pip \
        setuptools \
        virtualenv \
        pipenv \
    && pip3 list

# libindy
ARG LIBINDY_REPO
ARG LIBINDY_VERSION
ENV LIBINDY_REPO=${LIBINDY_REPO:-rc}
ENV LIBINDY_VERSION=${LIBINDY_VERSION:-1.14.3~127-xenial}

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial ${LIBINDY_REPO}" \
    && apt-get update && apt-get install -y \
        libindy=${LIBINDY_VERSION} \
    && rm -rf /var/lib/apt/lists/*

# get sdk repo
RUN git clone https://github.com/hyperledger/indy-sdk.git
