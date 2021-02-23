FROM teracy/ubuntu:16.04-dind-latest

ARG CLIENT_REPO_COMPONENT
RUN echo ${CLIENT_REPO_COMPONENT, "CLIENT_REPO_COMPONENT must be provided"}

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
RUN apt-get update && apt-get install -y \
        python3.5 \
        python3-pip \
        python-setuptools \
    && rm -rf /var/lib/apt/lists/*

# pypi based packages
# issues with pip>=10:
# https://github.com/pypa/pip/issues/5240
# https://github.com/pypa/pip/issues/5221
RUN python3 -m pip install -U \
        pip==10.0.0 \
        setuptools \
        virtualenv==16.0.0 \
        pipenv==2018.11.26 \
    && pip3 list

# sovrin repo init
ARG CLIENT_REPO_COMPONENT
RUN echo "Check that CLIENT_REPO_COMPONENT is provided" \
    && test -n "$CLIENT_REPO_COMPONENT"
ENV CLIENT_REPO_COMPONENT=${CLIENT_REPO_COMPONENT}

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && add-apt-repository "deb https://repo.sovrin.org/sdk/deb xenial ${CLIENT_REPO_COMPONENT}" \
    && apt-get update

# indy dependencies
ARG LIBINDY_VERSION
RUN echo "Check that LIBINDY_VERSION is provided" \
    && test -n "$LIBINDY_VERSION"
ENV LIBINDY_VERSION=${LIBINDY_VERSION}

RUN apt-get install -y \
        libindy=${LIBINDY_VERSION}

# TODO: Move to Sovrin tests
# sovrin dependencies
#ARG LIBSOVTOKEN_INSTALL
#ARG LIBSOVTOKEN_VERSION
#ENV LIBSOVTOKEN_INSTALL=$LIBSOVTOKEN_INSTALL
#ENV LIBSOVTOKEN_VERSION=${LIBSOVTOKEN_VERSION:-0.10.0~74}
#RUN if [ "$LIBSOVTOKEN_INSTALL" = "yes" ]; then \
#        apt-get update && apt-get install -y \
#            libsovtoken=${LIBSOVTOKEN_VERSION}; \
#        rm -rf /var/lib/apt/lists/*; \
#    fi

# repo cleanup
RUN add-apt-repository --remove "deb https://repo.sovrin.org/sdk/deb xenial ${CLIENT_REPO_COMPONENT}" \
    && rm -rf /var/lib/apt/lists/*

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
