FROM solita/ubuntu-systemd

ARG uid=1000

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
	&& rm -rf /var/lib/apt/lists/*

RUN pip3 install -U \
        'pip<10.0.0' \
        setuptools

ARG INDY_NODE_VERSION
ARG SOVTOKEN_VERSION
ARG SOVTOKENFEES_VERSION
ENV INDY_NODE_VERSION=${INDY_NODE_VERSION:-1.8.0~dev975}
ENV SOVTOKEN_VERSION=${SOVTOKEN_VERSION:-0.9.12~37}
ENV SOVTOKENFEES_VERSION=${SOVTOKENFEES_VERSION:-${SOVTOKEN_VERSION}}
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88 \
    && echo "deb https://repo.sovrin.org/deb xenial master" >> /etc/apt/sources.list \
    && apt-get update -y && apt-get install -y \
        indy-node=${INDY_NODE_VERSION} \
        sovtoken=${SOVTOKEN_VERSION} \
        sovtokenfees=${SOVTOKENFEES_VERSION} \
	&& rm -rf /var/lib/apt/lists/*

RUN echo " " >> /etc/indy/indy_config.py \
    && echo "NETWORK_NAME = 'sandbox'" >> /etc/indy/indy_config.py \
    && echo " " >> /etc/indy/indy_config.py
#    && echo "ForceViewChangeFreq = 1800" >> /etc/indy/indy_config.py \
#    && echo " " >> /etc/indy/indy_config.py

RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
COPY test_key.pub /root/.ssh/authorized_keys

#USER indy
#WORKDIR /home/indy
