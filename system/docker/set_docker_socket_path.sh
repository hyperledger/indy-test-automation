#!/bin/bash

docker_socket_path="/var/run/docker.sock"
docker_socket_mount_path=${docker_socket_path}
docker_socket_stat_path=${docker_socket_path}

if [[ "$IS_WSL" ||  "$WSL_DISTRO_NAME" ]]; then
    echo "Running on WSL2 ..."
    docker_socket_path="/${docker_socket_path}"
elif [[ "$OSTYPE" == "msys" ]]; then
    echo "Running on Windows ..."
    docker_socket_path="/${docker_socket_path}"
    docker_socket_stat_path="/c${docker_socket_stat_path}"
else
    echo "Running on linux/macOS ..."
fi