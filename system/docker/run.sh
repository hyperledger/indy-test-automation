#!/bin/bash

set -ex

if [ "$1" = "--help" ] ; then
  echo "Usage: $0 [test-target] [pytest-args] [network-name]"
  exit 0
fi

test_target="${1:-system/indy-node-tests}"
pytest_add_args="${2:-}"
network_name="${3:-indy-system-tests-network}"

repo_path=$(git rev-parse --show-toplevel)
docker_socket_path="/var/run/docker.sock"
user_id=$(id -u)
workdir_path="/tmp/indy-test-automation"
client_image_name="system-tests-client"
client_container_name="$client_image_name"

# 3. run client
docker run -it --rm --name "$client_container_name" \
    --network "${network_name}" \
    --ip "10.0.0.99" \
    --group-add $(stat -c '%g' "$docker_socket_path") \
    -v "$docker_socket_path:"$docker_socket_path \
    -v "$repo_path:$workdir_path" \
    -u "$user_id" \
    "$client_image_name" /bin/bash

# 4. create venv and install packages
#docker exec -t -w "$workdir_path" "$client_container_name" pipenv --three
#docker exec -t -w "$workdir_path" "$client_container_name" pipenv run pip install -r system/requirements.txt

# 5. run tests with env for network and subnet
#docker exec -it -w "$workdir_path" "$client_container_name" /bin/bash -c \
#    "INDY_SYSTEM_TESTS_NETWORK=$network_name pipenv run python -m pytest -l -v $pytest_add_args $test_target" || true

# 6. stop container
#docker rm -f "$client_container_name"
