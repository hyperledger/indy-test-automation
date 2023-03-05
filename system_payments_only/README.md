# System Payments Only Tests

This directory contains tests that still depend on the indy-sdk to work.  These tests are related to the Sovrin packages including the token plugins which have yet to be migrated to use the newer shared libraries.

## Environment variables

- `INDY_SYSTEM_TESTS_NETWORK`: a network name to use for created Indy Node pool, default: `indy-system-tests-network`
- `INDY_SYSTEM_TESTS_SUBNET`: an IP range in CIDR notation to use as subnet for the custom Indy Pool network, default: `10.0.0.0/24`

## `pytest` custom options

- '--payments': run payment tests as well, default: not set
- '--gatherlogs': gather node logs for failed tests, default: not set
- '--logsdir PATH': directory name to store node logs, default: `_build/logs`
