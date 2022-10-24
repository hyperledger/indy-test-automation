FROM teracy/ubuntu:20.04-dind-latest

# generally useful packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        openssl \
        gnupg \
        ca-certificates \
        apt-transport-https \
        software-properties-common \
        curl \
        wget \
        ssh \
        vim \
    && rm -rf /var/lib/apt/lists/*

# python
RUN apt-get update && apt-get install -y \
    python3-pip \
    python-setuptools \
    && rm -rf /var/lib/apt/lists/*

# pypi based packages
# issues with pip>=10:
# https://github.com/pypa/pip/issues/5240
# https://github.com/pypa/pip/issues/5221
RUN python3 -m pip install -U \
        'pip<10.0.0' \
        'setuptools<=50.3.2' \
        virtualenv==16.0.0 \
        pipenv==2018.11.26 \
    && pip3 list

RUN apt-get update -y && apt-get upgrade -y

# libindy
ARG LIBINDY_REPO_COMPONENT
ARG LIBINDY_VERSION
ENV LIBINDY_REPO_COMPONENT=${LIBINDY_REPO_COMPONENT:-master}
ENV LIBINDY_VERSION=${LIBINDY_VERSION:-1.10.0~1171}
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial ${CLIENT_REPO_COMPONENT}" \
    && echo "deb http://security.ubuntu.com/ubuntu bionic-security main"  >> /etc/apt/sources.list \
    && echo "deb https://repo.sovrin.org/sdk/deb bionic master" >> /etc/apt/sources.list \
    && apt-get update

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3BC8C2DD662F1C45 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 9692C00E657DDE61 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 
RUN add-apt-repository "deb https://sovrin.jfrog.io/artifactory/deb focal dev"
RUN add-apt-repository "deb https://hyperledger.jfrog.io/artifactory/indy focal dev rc" && apt-get update -y

# indy dependencies
ARG LIBINDY_VERSION
RUN : ${LIBINDY_VERSION:?"LIBINDY_VERSION must be provided"}
ENV LIBINDY_VERSION=${LIBINDY_VERSION}

RUN apt-get install -y \
    libssl1.0.0 \
    libssl1.1 \ 
    libindy=${LIBINDY_VERSION}

# TODO: Move to Sovrin tests
# sovrin dependencies
ARG LIBSOVTOKEN_INSTALL
ARG LIBSOVTOKEN_VERSION
ENV LIBSOVTOKEN_INSTALL=$LIBSOVTOKEN_INSTALL
ENV LIBSOVTOKEN_VERSION=${LIBSOVTOKEN_VERSION:-0.10.0~74}
RUN if [ "$LIBSOVTOKEN_INSTALL" = "yes" ]; then \
    apt-get update && apt-get install -y \
    libsovtoken=${LIBSOVTOKEN_VERSION}; \
    rm -rf /var/lib/apt/lists/*; \
    fi

# repo cleanup
RUN add-apt-repository --remove "deb https://repo.sovrin.org/sdk/deb xenial ${CLIENT_REPO_COMPONENT}" \
    && rm -rf /var/lib/apt/lists/*

# TODO workaround (suggested by http://click.pocoo.org/5/python3/)
# to use pipenv's dependency 'click' (http://click.pocoo.org)
# ? check for alternatives, is it still necessary
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

COPY test_key /root/.ssh/
RUN chmod 700 /root/.ssh/test_key \
    && chown 600 -R /root/.ssh

ENV IN_DOCKER_ENV yes

