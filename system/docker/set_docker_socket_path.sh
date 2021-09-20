#!/bin/bash

if [[ "$IS_WSL" ||  "$WSL_DISTRO_NAME" ]]; then
    echo "Running on WSL2"
    docker_socket_path="//var/run/docker.sock"
else
    echo "Running on linux/macOS"
    docker_socket_path="/var/run/docker.sock"
fi
