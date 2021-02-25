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

RUN pip3 install -U \
        'pip<10.0.0' \
        setuptools

ARG INDY_NODE_REPO_COMPONENT
ARG LIBINDY_CRYPTO_VERSION
ARG PYTHON3_LIBINDY_CRYPTO_VERSION
ARG INDY_PLENUM_VERSION
ARG INDY_NODE_VERSION
ENV INDY_NODE_REPO_COMPONENT=${INDY_NODE_REPO_COMPONENT:-rc}
ENV LIBINDY_CRYPTO_VERSION=${LIBINDY_CRYPTO_VERSION:-0.4.5}
ENV PYTHON3_LIBINDY_CRYPTO_VERSION=${PYTHON3_LIBINDY_CRYPTO_VERSION:-0.4.5}
ENV PYTHON3_PYZMQ_VERSION=${PYTHON3_PYZMQ_VERSION:-18.1.0}
ENV INDY_PLENUM_VERSION=${INDY_PLENUM_VERSION:-1.12.2}
ENV INDY_NODE_VERSION=${INDY_NODE_VERSION:-1.12.2~rc1}
# ENV INDY_NODE_REPO_COMPONENT=${INDY_NODE_REPO_COMPONENT:-master}
# ENV LIBINDY_CRYPTO_VERSION=${LIBINDY_CRYPTO_VERSION:-0.4.5}
# ENV PYTHON3_LIBINDY_CRYPTO_VERSION=${PYTHON3_LIBINDY_CRYPTO_VERSION:-0.4.5}
# ENV PYTHON3_PYZMQ_VERSION=${PYTHON3_PYZMQ_VERSION:-18.1.0}
# ENV INDY_PLENUM_VERSION=${INDY_PLENUM_VERSION:-1.13.0~dev1012}
# ENV INDY_NODE_VERSION=${INDY_NODE_VERSION:-1.13.0~dev1199}
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CE7709D068DB5E88 \
    && echo "deb https://repo.sovrin.org/deb xenial ${INDY_NODE_REPO_COMPONENT}" >> /etc/apt/sources.list \
    && apt-get update -y && apt-get install -y \
        libindy-crypto=${LIBINDY_CRYPTO_VERSION} \
        python3-indy-crypto=${PYTHON3_LIBINDY_CRYPTO_VERSION} \
        python3-pyzmq=${PYTHON3_PYZMQ_VERSION} \
        indy-plenum=${INDY_PLENUM_VERSION} \
        indy-node=${INDY_NODE_VERSION} \
	&& rm -rf /var/lib/apt/lists/*

# sovrin & token plugins
# FIXME
#   - for now it's tricky to set proper versions for master artifacts
#   - defaults are for stable
ARG TOKEN_PLUGINS_INSTALL
ARG SOVRIN_VERSION
ARG SOVTOKEN_VERSION
ARG SOVTOKENFEES_VERSION
ENV TOKEN_PLUGINS_INSTALL=$TOKEN_PLUGINS_INSTALL
ENV SOVRIN_VERSION=${SOVRIN_VERSION:-1.1.69}
ENV SOVTOKEN_VERSION=${SOVTOKEN_VERSION:-1.0.8~dev151}
# ENV SOVRIN_VERSION=${SOVRIN_VERSION:-1.1.207}
# ENV SOVTOKEN_VERSION=${SOVTOKEN_VERSION:-1.0.8~dev150}
ENV SOVTOKENFEES_VERSION=${SOVTOKENFEES_VERSION:-${SOVTOKEN_VERSION}}
#RUN if [ "$TOKEN_PLUGINS_INSTALL" = "yes" ]; then \
RUN \
        set -ex; \
        apt-get update && apt-get install -y \
            sovrin=${SOVRIN_VERSION} \
            sovtoken=${SOVTOKEN_VERSION} \
            sovtokenfees=${SOVTOKENFEES_VERSION}; \
        rm -rf /var/lib/apt/lists/*; \
    fi

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
