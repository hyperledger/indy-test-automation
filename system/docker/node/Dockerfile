FROM solita/ubuntu-systemd

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
    ssh \
    vim \
    mc \
    stress \
    dbus \
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
# sovrin & token plugins
ARG SOVRIN_INSTALL
ARG SOVRIN_VERSION
ENV SOVRIN_INSTALL=$SOVRIN_INSTALL
ENV SOVRIN_VERSION=${SOVRIN_VERSION:-1.1.69}
COPY . . 
RUN if [ "$SOVRIN_INSTALL" = "yes" ]; then \
    dpkg -i "sovrin_${SOVRIN_VERSION}_amd64.deb"; \
    fi

# repo cleanup
RUN sed '/deb https:\/\/repo.sovrin.org\/sdk\/deb xenial ${NODE_REPO_COMPONENT}/d' /etc/apt/sources.list \
    && rm -rf /var/lib/apt/lists/*

# network config
RUN echo " " >> /etc/indy/indy_config.py \
    && echo "NETWORK_NAME = 'sandbox'" >> /etc/indy/indy_config.py \
    && echo " " >> /etc/indy/indy_config.py \
    && echo "logLevel = 0" >> /etc/indy/indy_config.py \
    && echo " " >> /etc/indy/indy_config.py

RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
COPY test_key.pub /root/.ssh/authorized_keys
## hotfix indy-node-control files here
#COPY node_control_utils_1_1_35.py /usr/local/lib/python3.5/dist-packages/indy_node/utils/node_control_utils.py
#RUN chmod 644 /usr/local/lib/python3.5/dist-packages/indy_node/utils/node_control_utils.py \
#    && chown root:root /usr/local/lib/python3.5/dist-packages/indy_node/utils/node_control_utils.py