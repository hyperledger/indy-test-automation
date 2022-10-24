#!/bin/bash

set -o errexit
set -o pipefail
#set -o nounset
set -o xtrace

export MSYS_NO_PATHCONV=1
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
docker_routine_path="$repo_path/system_node_only/docker"

# Set the following variables based on the OS:
# - docker_socket_path
# - docker_socket_mount_path
# - $docker_socket_user_group
. set_docker_socket_path.sh

image_repository="hyperledger/indy-test-automation"
docker_compose_image_name="${image_repository}:docker-compose"

node_env_variables=" \
    NODE_REPO_COMPONENT \
    NODE_SOVRIN_REPO_COMPONENT \
    INDY_PLENUM_VERSION \
    INDY_NODE_VERSION \
    UBUNTU_VERSION \
    PYTHON3_PYZMQ_VERSION \
    URSA_VERSION \
"

echo "Docker version..."
docker version

set +x
echo "Environment env variables..."
for i in $node_env_variables
do
    echo "$i=${!i}"
done
set -x

# 1. build docker-compose image
# TODO pass optional docker composer version
docker build -t "$docker_compose_image_name" "$docker_routine_path/docker-compose"

# 3. build node image
docker run -t --rm \
    --group-add $docker_socket_user_group \
    -v "$docker_socket_path:"$docker_socket_mount_path \
    -v "$repo_path:$workdir_path" \
    -w "$workdir_path" \
    -u "$user_id" \
    -e "IMAGE_REPOSITORY=$image_repository" \
    -e u_id="$user_id" \
    -e NODE_REPO_COMPONENT \
    -e INDY_NODE_VERSION \
    -e INDY_PLENUM_VERSION \
    -e URSA_VERSION \
    -e PYTHON3_PYZMQ_VERSION \
    -e NODE_SOVRIN_REPO_COMPONENT \
    -e UBUNTU_VERSION \
    "$docker_compose_image_name" docker-compose -f system_node_only/docker/docker-compose.yml build node
    
docker images "$image_repository"

# 4. clean existing environment
$docker_routine_path/clean.sh "$test_network_name"

# 5. remove test network if exists
docker network ls -q --filter name="$test_network_name" | xargs -r docker network rm

# 6. create test network
docker network create --subnet="$test_network_subnet" "$test_network_name"
docker network ls
docker inspect "$test_network_name"