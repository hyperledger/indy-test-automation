#!/bin/bash

function usage {
  echo "Usage: $0 test-network-name test-network-subnet"
}

if [ "$1" = "--help" ] ; then
    usage
    exit 0
fi

if [[ $# -ne 2 ]]; then
    echo "Illegal number of arguments"
    usage
    exit 1
fi

set -ex

test_network_name="$1"
test_network_subnet="$2"

user_id=$(id -u)
repo_path=$(git rev-parse --show-toplevel)
docker_routine_path="$repo_path/system/docker"

docker_socket_path="/var/run/docker.sock"
workdir_path="/tmp/indy-test-automation"
docker_compose_image_name="hyperledger/indy-test-automation:docker-compose"

# 1. build docker-compose image
# TODO pass optional docker composer version
docker build -t "$docker_compose_image_name" "$docker_routine_path/docker-compose"

# 2. build client image
docker run -it --rm \
    --group-add $(stat -c '%g' "$docker_socket_path") \
    -v "$docker_socket_path:"$docker_socket_path \
    -v "$repo_path:$workdir_path" \
    -w "$workdir_path" \
    -u "$user_id" \
    -e u_id="$user_id" \
    -e PYTHON3_VERSION \
    -e LIBINDY_REPO_COMPONENT \
    -e LIBINDY_VERSION \
    -e LIBSOVTOKEN_VERSION \
    "$docker_compose_image_name" docker-compose -f system/docker/docker-compose.yml build client

# 3. build node image
docker run -it --rm \
    --group-add $(stat -c '%g' "$docker_socket_path") \
    -v "$docker_socket_path:"$docker_socket_path \
    -v "$repo_path:$workdir_path" \
    -w "$workdir_path" \
    -u "$user_id" \
    -e u_id="$user_id" \
    -e INDY_NODE_REPO_COMPONENT \
    -e LIBINDY_CRYPTO_VERSION \
    -e PYTHON3_LIBINDY_CRYPTO_VERSION \
    -e INDY_PLENUM_VERSION \
    -e INDY_NODE_VERSION \
    -e SOVTOKEN_VERSION \
    -e SOVTOKENFEES_VERSION \
    "$docker_compose_image_name" docker-compose -f system/docker/docker-compose.yml build node

# 4. clean existing envronment
$docker_routine_path/clean.sh "$test_network_name"

# 5. remove test network if exists
docker network ls -q --filter name="$test_network_name" | xargs -r docker network rm

# 6. create test network
docker network create --subnet="$test_network_subnet" "$test_network_name"
