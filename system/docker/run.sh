#!/bin/bash

export MSYS_NO_PATHCONV=1
DEF_TEST_TARGET="system/indy-node-tests"
DEF_PYTEST_ARGS="-l -v"
DEF_TEST_NETWORK_NAME="indy-test-automation-network"


function usage {
  echo "\
Usage: $0 [test-target] [pytest-args] [test-network-name] [image-repository] [client-image-name] [node-image-name]
defaults:
    - test-target: '${DEF_TEST_TARGET}'
    - pytest-args: '${DEF_PYTEST_ARGS}'
    - test-network-name: '${DEF_TEST_NETWORK_NAME}'"
}

if [ "$1" = "--help" ] ; then
    usage
    exit 0
fi

set -ex

test_target="${1:-$DEF_TEST_TARGET}"
pytest_args="${2:-$DEF_PYTEST_ARGS}"
test_network_name="${3:-$DEF_TEST_NETWORK_NAME}"

# Set the name of the output file of tests
cd ../..
if [[ -d $test_target ]]; then
    echo "$test_target is a directory"
    test_output_file="test-result-indy-test-automation.txt"
elif [[ -f $test_target ]]; then
    echo "$test_target is a file"
    test_name=$(echo $test_target | sed -nr 's;.*tests/(.*).py.*;\1;p')
    test_output_file="test-result-indy-test-automation-${test_name}.txt"
else
    echo "$test_target is not valid"
    exit 1
fi
cd -


repo_path=$(git rev-parse --show-toplevel)
user_id=$(id -u)
group_id=$(id -g)

# Set the following variables based on the OS:
# - docker_socket_path
# - docker_socket_mount_path
# - $docker_socket_user_group
. set_docker_socket_path.sh

workdir_path="/tmp/indy-test-automation"

image_repository=${IMAGE_REPOSITORY:="hyperledger/indy-test-automation"}
client_image=${CLIENT_IMAGE:=":client-${UBUNTU_VERSION}"}
client_image_name="${image_repository}${client_image}"
node_image=${NODE_IMAGE:=":node-${UBUNTU_VERSION}"}
node_image_name="${image_repository}${node_image}"
ubuntu_version="${UBUNTU_VERSION}" 
client_container_name="indy-test-automation-client"

node_env_variables=" \
    IMAGE_REPOSITORY \
    UBUNTU_VERSION \
"
echo "Environment env variables..."
for i in $node_env_variables
do
    echo "$i=${!i}"
done



command_setup="
    set -ex
    pip3 install --user pipenv
    pipenv --three
    # We need this because pipenv installs the latest version of pip by default.
    # The latest version of pip requires the version in pypi exactly match the version in package's setup.py file.
    # But they don't match for python3-indy... so we need to have the old version of pip pinned.
    pipenv run pip install pip==10.0.1
    pipenv run pip install -r system/requirements-${ubuntu_version}.txt
"


command_run="
    pipenv run python -m pytest $pytest_args $test_target > $test_output_file
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

# Run tests
docker run $docker_opts --rm --privileged --name "$client_container_name" \
    --network "${test_network_name}" \
    --ip "10.0.0.99" \
    --group-add $docker_socket_user_group \
    -v "$docker_socket_path:"$docker_socket_mount_path \
    -v "$repo_path:$workdir_path" \
    -v "/tmp:/tmp" \
    -w "$workdir_path" \
    -e "INDY_SYSTEM_TESTS_NETWORK=$test_network_name" \
    -e "INDY_SYSTEM_TESTS_DOCKER_NAME=$node_image_name" \
    "$client_image_name" /bin/bash -c "$run_command"