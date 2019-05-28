#!/bin/bash

set -ex

if [ "$1" = "--help" ] ; then
  echo "Usage: $0 [network-name]"
  exit 0
fi

network_name="${1:-indy-system-tests-network}"

repo_path=$(git rev-parse --show-toplevel)
docker_routine_path="$repo_path/system/docker/client"
# TODO limit subnet range to reduce risk of overlapping with system resources
network_subnet="10.0.0.0/24"
client_image_name="system-tests-client"


# 1. build client image
docker build -t "$client_image_name" -f "$docker_routine_path/Dockerfile" "$docker_routine_path"
# 2. create network
#   remove test network if exists
docker network ls -q --filter name="$network_name" | xargs -r docker network rm
#   create test network
docker network create --subnet="$network_subnet" "$network_name"
