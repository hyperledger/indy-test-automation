FROM teracy/ubuntu:16.04-dind-latest

# generally useful packages
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        apt-transport-https \
        software-properties-common \
        curl \
        wget \
        ssh \
        vim \
    && rm -rf /var/lib/apt/lists/*

# python
ARG PYTHON3_VERSION
ENV PYTHON3_VERSION=${PYTHON3_VERSION:-3.5}
RUN apt-get update && apt-get install -y \
        python${PYTHON3_VERSION} \
        python3-pip \
        python-setuptools \
    && rm -rf /var/lib/apt/lists/*

# pypi based packages
# issues with pip>=10:
# https://github.com/pypa/pip/issues/5240
# https://github.com/pypa/pip/issues/5221
RUN python3 -m pip install -U \
        pip \
        setuptools \
        virtualenv==16.0.0 \
        pipenv==2018.11.26 \
    && pip3 list

# libindy
ARG LIBINDY_REPO_COMPONENT
ARG LIBINDY_VERSION
ENV LIBINDY_REPO_COMPONENT=${LIBINDY_REPO_COMPONENT:-master}
ENV LIBINDY_VERSION=${LIBINDY_VERSION:-1.10.0~1171}
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial ${LIBINDY_REPO_COMPONENT}" \
    && apt-get update && apt-get install -y \
        libindy=${LIBINDY_VERSION} \
    && rm -rf /var/lib/apt/lists/*

# libsovtoken
# FIXME
#   - for now it's tricky to set proper version for master artifacts
#   - defaults are for stable
ARG LIBSOVTOKEN_INSTALL
ARG LIBSOVTOKEN_VERSION
ENV LIBSOVTOKEN_INSTALL=$LIBSOVTOKEN_INSTALL
ENV LIBSOVTOKEN_VERSION=${LIBSOVTOKEN_VERSION:-0.10.0~74}
RUN if [ "$LIBSOVTOKEN_INSTALL" = "yes" ]; then \
        set -ex; \
        apt-get update && apt-get install -y \
            libsovtoken=${LIBSOVTOKEN_VERSION}; \
        rm -rf /var/lib/apt/lists/*; \
    fi

# user
ARG u_id=1000
ARG u_name=user

RUN if [ "$u_id" != "0" ]; then \
        useradd -ms /bin/bash -u $u_id $u_name; \
    fi

# TODO workaround (suggested by http://click.pocoo.org/5/python3/)
# to use pipenv's dependency 'click' (http://click.pocoo.org)
# ? check for alternatives, is it still necessary
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# init ssh env
COPY test_key /home/$u_name/.ssh/
RUN chmod 0400 /home/$u_name/.ssh/test_key \
    && chown -R $u_name:$u_name /home/$u_name/.ssh

ENV IN_DOCKER_ENV yes

USER $u_id
WORKDIR /home/$u_name
