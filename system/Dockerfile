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
COPY test_key.pub /root/.ssh/authorized_keys
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 68DB5E88
RUN echo "deb https://repo.sovrin.org/deb xenial master" >> /etc/apt/sources.list
RUN useradd -ms /bin/bash -l -u $uid indy
RUN apt-get update -y && apt-get install -y indy-node=1.8.0~dev932 indy-plenum=1.8.0~dev791 sovtoken=0.9.6~25 sovtokenfees=0.9.6~25
RUN echo " " >> /etc/indy/indy_config.py \
    && echo "NETWORK_NAME = 'sandbox'" >> /etc/indy/indy_config.py \
    && echo " " >> /etc/indy/indy_config.py \
    && echo "logLevel = 0" >> /etc/indy/indy_config.py \
    && echo " " >> /etc/indy/indy_config.py
#USER indy
#WORKDIR /home/indy