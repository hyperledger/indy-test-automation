FROM indycore_for_chaos

ARG ips
ARG priv_key

USER root

RUN cd ~ && git clone https://github.com/hyperledger/indy-test-automation.git
RUN apt-get update -y && apt-get install -y sudo libssl-dev libyaml-dev
RUN cd ~/indy-test-automation/chaos && python3 setup.py develop
RUN apt-get update -y && apt-get install -y ssh
RUN mkdir /root/.ssh
COPY $priv_key /root/.ssh/dockerkey
COPY ./config /root/.ssh/config
RUN chmod g-rwx /root/.ssh/dockerkey
RUN cp /var/lib/indy/sandbox/pool_transactions_genesis ~

CMD /bin/bash