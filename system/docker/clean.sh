#!/bin/bash

DEF_TEST_NETWORK_NAME="indy-test-automation-network"

function usage {
  echo "\
Usage: $0 [test-network-name]
defaults:
    - test-network-name: '${DEF_TEST_NETWORK_NAME}'\
"
}

if [ "$1" = "--help" ] ; then
    usage
    exit 0
fi

set -ex

test_network_name="${1:-$DEF_TEST_NETWORK_NAME}"

# 1. removes all containers attached to the test network
docker ps -a --filter network=$test_network_name
docker ps -q --filter network=$test_network_name | xargs -r docker rm -f
docker ps -a --filter network=$test_network_name


# 2. removes test network
docker network ls
docker network ls -q --filter name="$test_network_name" | xargs -r docker network rm
docker network ls
