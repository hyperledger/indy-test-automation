# System Tests for Indy Node without Sovrin dependencies

## Environment variables

- `INDY_SYSTEM_TESTS_NETWORK`: a network name to use for created Indy Node pool, default: `indy-system-tests-network`
- `INDY_SYSTEM_TESTS_SUBNET`: an IP range in CIDR notation to use as subnet for the custom Indy Pool network, default: `10.0.0.0/24`

## `pytest` custom options

- '--payments': run payment tests as well, default: not set
- '--gatherlogs': gather node logs for failed tests, default: not set
- '--logsdir PATH': directory name to store node logs, default: `_build/logs`

## Similarities between ./system and ./system_node_only
Most of the files in `./system` and `./system_node_only` are the same and the file that changed contains some adjustments to run the tests without sovrin dependencies and to run the tests in a GitHub Action pipeline. 
The overall structure of how the testing works remained the same. It is still based on docker-in-docker (DinD) and a systemd container.

## Differences between ./system and ./system_node_only
The `./system_node_only` folder contains the following changes:
- The config has been extended to run in a GitHub Actions pipeline
- The sovrin dependencies have been removed in the docker images as well in the tests
- The repo for `indy-node` and `indy-plenum` changed from the sovrin repo to the Hyperledger Artifactory
- The foundation for the Ubuntu 20.04 version of Indy is created (still WIP) 