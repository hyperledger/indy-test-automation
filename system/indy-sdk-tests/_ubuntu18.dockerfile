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
    && add-apt-repository "deb https://repo.sovrin.org/sdk/deb bionic test" \
    && apt-get update && apt-get install -y \
        libindy=1.10.1~8 \
        indy-cli=1.10.1~8 \
        libnullpay=1.10.1~8 \
        libvcx=0.3.2~8 \
    && rm -rf /var/lib/apt/lists/*