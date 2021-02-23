FROM teracy/ubuntu:16.04-dind-latest

ARG DOCKER_COMPOSE_VERSION
ENV DOCKER_COMPOSE_VERSION=${DOCKER_COMPOSE_VERSION:-1.24.0}
RUN curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-`uname -s`-`uname -m`"  -o  /usr/local/bin/docker-compose \
    && chmod +x /usr/local/bin/docker-compose
