#!/bin/bash

set -o errexit
set -o pipefail
#set -o nounset
set -o xtrace

DEF_TEST_NETWORK_NAME="indy-test-automation-network"
# TODO limit default subnet range to reduce risk of overlapping with system resources
DEF_TEST_NETWORK_SUBNET="10.0.0.0/24"

function usage {
  echo "\
Usage: $0 [test-network-name] [test-network-subnet]
defaults:
    - test-network-name: '${DEF_TEST_NETWORK_NAME}'
    - test-network-subnet: '${DEF_TEST_NETWORK_SUBNET}'\
"
}

if [ "$1" = "--help" ] ; then
    usage
    exit 0
fi

test_network_name="${1:-$DEF_TEST_NETWORK_NAME}"
test_network_subnet="${2:-$DEF_TEST_NETWORK_SUBNET}"

user_id=$(id -u)
repo_path=$(git rev-parse --show-toplevel)
docker_routine_path="$repo_path/system/docker"

docker_socket_path="/var/run/docker.sock"
workdir_path="/tmp/indy-test-automation"

image_repository="hyperledger/indy-test-automation"
docker_compose_image_name="${image_repository}:docker-compose"

client_env_variables=" \
    CLIENT_REPO_COMPONENT \
    LIBINDY_CRYPTO_VERSION \
    LIBSOVTOKEN_INSTALL \
    LIBSOVTOKEN_VERSION \
"

echo "Docker version..."
docker version

set +x
echo "Environment env variables..."
for i in $client_env_variables
do
    echo "$i=${!i}"
done
set -x

# 1. build docker-compose image
# TODO pass optional docker composer version
docker build -t "$docker_compose_image_name" "$docker_routine_path/docker-compose"

# 2. build client image
docker run -t --rm \
    --group-add $(stat -c '%g' "$docker_socket_path") \
    -v "$docker_socket_path:"$docker_socket_path \
    -v "$repo_path:$workdir_path" \
    -w "$workdir_path" \
    -u "$user_id" \
    -e "IMAGE_REPOSITORY=$image_repository" \
    -e u_id="$user_id" \
    -e CLIENT_REPO_COMPONENT \
    -e LIBINDY_VERSION \
    -e LIBSOVTOKEN_INSTALL \
    -e LIBSOVTOKEN_VERSION \
    "$docker_compose_image_name" docker-compose -f system/docker/docker-compose.yml build client

docker images "$image_repository"

# 4. clean existing environment
$docker_routine_path/clean.sh "$test_network_name"

# 5. remove test network if exists
docker network ls -q --filter name="$test_network_name" | xargs -r docker network rm

# 6. create test network
docker network create --subnet="$test_network_subnet" "$test_network_name"
docker network ls
docker inspect "$test_network_name"