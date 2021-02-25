FROM solita/ubuntu-systemd

# Install environment
RUN apt-get update -y && apt-get install -y \
        git \
        wget \
        python3.5 \
        python3-pip \
        python-setuptools \
        python3-nacl \
        apt-transport-https \
        ca-certificates \
        ssh \
        vim \
        mc \
        stress \
	&& rm -rf /var/lib/apt/lists/*

# pip<10.0.0 is important. pip==10.0.0 doesn't work.
RUN pip3 install -U \
        'pip<10.0.0' \
        setuptools

# sovrin repo init
ARG NODE_REPO_COMPONENT
RUN : ${NODE_REPO_COMPONENT:?"NODE_REPO_COMPONENT must be provided"}
ENV NODE_REPO_COMPONENT=${NODE_REPO_COMPONENT}

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && echo "deb https://repo.sovrin.org/deb xenial ${NODE_REPO_COMPONENT}" >> /etc/apt/sources.list \
    && apt-get update -y

# indy depedencies
ARG LIBINDY_CRYPTO_VERSION
RUN : ${LIBINDY_CRYPTO_VERSION:?"LIBINDY_CRYPTO_VERSION must be provided"}
ENV LIBINDY_CRYPTO_VERSION=${LIBINDY_CRYPTO_VERSION}

ARG PYTHON3_LIBINDY_CRYPTO_VERSION
RUN : ${PYTHON3_LIBINDY_CRYPTO_VERSION:?"PYTHON3_LIBINDY_CRYPTO_VERSION must be provided"}
ENV PYTHON3_LIBINDY_CRYPTO_VERSION=${PYTHON3_LIBINDY_CRYPTO_VERSION}

ARG PYTHON3_PYZMQ_VERSION
RUN : ${PYTHON3_PYZMQ_VERSION:?"PYTHON3_PYZMQ_VERSION must be provided"}
ENV PYTHON3_PYZMQ_VERSION=${PYTHON3_PYZMQ_VERSION}

ARG INDY_PLENUM_VERSION
RUN : ${INDY_PLENUM_VERSION:?"INDY_PLENUM_VERSION must be provided"}
ENV INDY_PLENUM_VERSION=${INDY_PLENUM_VERSION}

ARG INDY_NODE_VERSION
RUN : ${INDY_NODE_VERSION:?"INDY_NODE_VERSION must be provided"}
ENV INDY_NODE_VERSION=${INDY_NODE_VERSION}

RUN apt-get install -y \
        libindy-crypto=${LIBINDY_CRYPTO_VERSION} \
        python3-indy-crypto=${PYTHON3_LIBINDY_CRYPTO_VERSION} \
        python3-pyzmq=${PYTHON3_PYZMQ_VERSION} \
        indy-plenum=${INDY_PLENUM_VERSION} \
        indy-node=${INDY_NODE_VERSION}

# TODO: Move to Sovrin tests
# sovrin & token plugins
# FIXME
#   - for now it's tricky to set proper versions for master artifacts
#   - defaults are for stable
#ARG TOKEN_PLUGINS_INSTALL
#ARG SOVRIN_VERSION
#ARG SOVTOKEN_VERSION
#ARG SOVTOKENFEES_VERSION
#ENV TOKEN_PLUGINS_INSTALL=$TOKEN_PLUGINS_INSTALL
#ENV SOVRIN_VERSION=${SOVRIN_VERSION:-1.1.69}
#ENV SOVTOKEN_VERSION=${SOVTOKEN_VERSION:-1.0.7~rc32}
#ENV SOVTOKENFEES_VERSION=${SOVTOKENFEES_VERSION:-${SOVTOKEN_VERSION}}
#RUN if [ "$TOKEN_PLUGINS_INSTALL" = "yes" ]; then \
#        set -ex; \
#        apt-get update && apt-get install -y \
#            sovrin=${SOVRIN_VERSION} \
#            sovtoken=${SOVTOKEN_VERSION} \
#            sovtokenfees=${SOVTOKENFEES_VERSION}; \
#        rm -rf /var/lib/apt/lists/*; \
#    fi

# repo cleanup
RUN add-apt-repository --remove "deb https://repo.sovrin.org/sdk/deb xenial ${NODE_REPO_COMPONENT}" \
    && rm -rf /var/lib/apt/lists/*

# network config
RUN echo " " >> /etc/indy/indy_config.py \
    && echo "NETWORK_NAME = 'sandbox'" >> /etc/indy/indy_config.py \
    && echo " " >> /etc/indy/indy_config.py \
    && echo "logLevel = 0" >> /etc/indy/indy_config.py \
    && echo " " >> /etc/indy/indy_config.py

RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
COPY test_key.pub /root/.ssh/authorized_keys
