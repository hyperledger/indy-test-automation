FROM indybase

ARG uid=1000
ARG pub_key

RUN apt-get update -y && apt-get install -y ssh
RUN mkdir /root/.ssh
COPY $pub_key /root/.ssh/authorized_keys

RUN service ssh start