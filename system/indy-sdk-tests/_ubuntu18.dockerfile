FROM ubuntu:18.04

# generally useful packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        apt-transport-https \
        software-properties-common \
        curl \
        wget \
        ssh \
        vim \
        dirmngr \
        gpg-agent \
    && rm -rf /var/lib/apt/lists/*

# bionic SDK installation
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/sdk/deb bionic rc" \
    && apt-get update && apt-get install -y \
        libindy=1.14.3~127-bionic \
        indy-cli=1.14.3~127-bionic \
        libnullpay=1.14.3~127-bionic \
        libvcx=0.7.0~127-bionic \
    && rm -rf /var/lib/apt/lists/*