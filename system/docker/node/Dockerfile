FROM jrei/systemd-ubuntu:20.04

ARG uid=1000
ARG user=indy

# Install environment
RUN apt-get update -y && apt-get install -y \
    git \
    wget \
    python3-pip \
    python3-nacl \
    python-setuptools \
    python3-nacl \
    apt-transport-https \
    ca-certificates \
    software-properties-common \
    ssh \
    vim \
    mc \
    stress \
    dbus \
    && rm -rf /var/lib/apt/lists/*

# pip<10.0.0 is important. pip==10.0.0 doesn't work.
RUN pip3 install -U \
        'pip<10.0.0' \
        'setuptools<=50.3.2'

# sovrin repo init
ARG NODE_REPO_COMPONENT
RUN : ${NODE_REPO_COMPONENT:?"NODE_REPO_COMPONENT must be provided"}
ENV NODE_REPO_COMPONENT=${NODE_REPO_COMPONENT}

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 3BC8C2DD662F1C45 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 9692C00E657DDE61 && \
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 
RUN echo "deb https://repo.sovrin.org/deb bionic ${NODE_REPO_COMPONENT}" >> /etc/apt/sources.list && \
    echo "deb http://security.ubuntu.com/ubuntu bionic-security main"  >> /etc/apt/sources.list && \
    echo "deb https://repo.sovrin.org/sdk/deb bionic master" >> /etc/apt/sources.list
RUN add-apt-repository "deb https://sovrin.jfrog.io/artifactory/deb focal dev"
RUN add-apt-repository "deb https://hyperledger.jfrog.io/artifactory/indy focal dev rc"
RUN printf '%s\n%s\n%s\n' 'Package: *' 'Pin: origin hyperledger.jfrog.io' 'Pin-Priority: 1001' >> /etc/apt/preferences && \
    apt-get update -y

# indy depedencies
ARG URSA_VERSION
RUN : ${URSA_VERSION:?"URSA_VERSION must be provided"}
ENV URSA_VERSION=${URSA_VERSION}

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
    ursa=${URSA_VERSION} \
    libssl1.1 \
    python3-pyzmq=${PYTHON3_PYZMQ_VERSION} \
    indy-plenum=${INDY_PLENUM_VERSION} \
    python3-importlib-metadata=3.10.1 \
    rocksdb=5.8.8 \
    python3-rocksdb \
    python3-ujson=1.33 \
    indy-node=${INDY_NODE_VERSION}
# sovrin & token plugins
ARG SOVRIN_INSTALL
ARG SOVRIN_VERSION
ENV SOVRIN_INSTALL=$SOVRIN_INSTALL
ENV SOVRIN_VERSION=${SOVRIN_VERSION:-1.1.69}
COPY . . 
RUN if [ "$SOVRIN_INSTALL" = "yes" ]; then \
    dpkg -i "sovrin_${SOVRIN_VERSION}_amd64.deb"; \
    fi

ARG SOVTOKEN_VERSION
ARG SOVTOKENFEES_VERSION
ENV SOVTOKEN_VERSION=${SOVTOKEN_VERSION:-1.2.0-dev1666268500}
ENV SOVTOKENFEES_VERSION=${SOVTOKENFEES_VERSION:-${SOVTOKEN_VERSION}}
RUN if [ "$TOKEN_PLUGINS_INSTALL" = "yes" ]; then \
# RUN \
        set -ex; \
        apt-get update && apt-get install -y \
            sovrin=${SOVRIN_VERSION} \
            sovtoken=${SOVTOKEN_VERSION} \
            sovtokenfees=${SOVTOKENFEES_VERSION}; \
        rm -rf /var/lib/apt/lists/*; \
    fi

# network config
RUN echo " " >> /etc/indy/indy_config.py \
    && echo "NETWORK_NAME = 'sandbox'" >> /etc/indy/indy_config.py \
    && echo " " >> /etc/indy/indy_config.py \
    && echo "logLevel = 0" >> /etc/indy/indy_config.py \
    && echo " " >> /etc/indy/indy_config.py

# Server side ssh configuration
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
COPY test_key.pub /root/.ssh/authorized_keys
RUN chmod 700 /root/.ssh && \
    chmod 600 /root/.ssh/authorized_keys

## hotfix indy-node-control files here
#COPY node_control_utils_1_1_35.py /usr/local/lib/python3.5/dist-packages/indy_node/utils/node_control_utils.py
#RUN chmod 644 /usr/local/lib/python3.5/dist-packages/indy_node/utils/node_control_utils.py \
#    && chown root:root /usr/local/lib/python3.5/dist-packages/indy_node/utils/node_control_utils.py