#!/bin/bash

function usage {
  echo "Usage: $0 test-network-name"
}

if [ "$1" = "--help" ] ; then
    usage
    exit 0
fi

if [[ $# -ne 1 ]]; then
    echo "Illegal number of arguments"
    usage
    exit 1
fi

set -ex

test_network_name="$1"

# 1. removes all containers attached to the test network
docker ps -q --filter network=$networkName | xargs -r docker rm -f

# 2. removes test network
docker network ls -q --filter name="$test_network_name" | xargs -r docker network rm
