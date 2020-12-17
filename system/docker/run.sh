#!/bin/bash

DEF_TEST_TARGET="system/indy-node-tests"
DEF_PYTEST_ARGS="-l -v"
DEF_TEST_NETWORK_NAME="indy-test-automation-network"

function usage {
  echo "\
Usage: $0 [test-target] [pytest-args] [test-network-name]
defaults:
    - test-target: '${DEF_TEST_TARGET}'
    - pytest-args: '${DEF_PYTEST_ARGS}'
    - test-network-name: '${DEF_TEST_NETWORK_NAME}'
"
}

if [ "$1" = "--help" ] ; then
    usage
    exit 0
fi

set -ex

test_target="${1:-$DEF_TEST_TARGET}"
pytest_args="${2:-$DEF_PYTEST_ARGS}"
test_network_name="${3:-$DEF_TEST_NETWORK_NAME}"

repo_path=$(git rev-parse --show-toplevel)
user_id=$(id -u)
group_id=$(id -g)
docker_socket_path="/var/run/docker.sock"
workdir_path="/tmp/indy-test-automation"

image_repository="hyperledger/indy-test-automation"
client_image_name="${image_repository}:client"
client_container_name="indy-test-automation-client"

command_setup="
    set -ex
    pipenv --three
    # We need this because pipenv installs the latest version of pip by default.
    # The latest version of pip requires the version in pypi exactly match the version in package's setup.py file.
    # But they don't match for python3-indy... so we need to have the old version of pip pinned.
    pipenv run pip install pip==10.0.1
    pipenv run pip install -r system/requirements.txt
"

command_run="
    pipenv run python -m pytest $pytest_args $test_target
"

if [ "$INDY_SYSTEM_TESTS_MODE" = "debug" ] ; then
    docker_opts="-it"
    run_command="
        $command_setup
        echo '$command_run'
        bash"
else
    docker_opts="-t"
    run_command="
        $command_setup
        $command_run"
fi

# TODO pass specified env variables
docker run $docker_opts --rm --name "$client_container_name" \
    --network "${test_network_name}" \
    --ip "10.0.0.99" \
    --group-add $(stat -c '%g' "$docker_socket_path") \
    -v "$docker_socket_path:"$docker_socket_path \
    -v "$repo_path:$workdir_path" \
    -v "/tmp:/tmp" \
    -u "$user_id:$group_id" \
    -w "$workdir_path" \
    -e "INDY_SYSTEM_TESTS_NETWORK=$test_network_name" \
    "$client_image_name" /bin/bash -c "$run_command"
