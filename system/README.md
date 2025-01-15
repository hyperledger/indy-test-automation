# System Tests

## Environment variables

- `INDY_SYSTEM_TESTS_NETWORK`: a network name to use for created Indy Node pool, default: `indy-system-tests-network`
- `INDY_SYSTEM_TESTS_SUBNET`: an IP range in CIDR notation to use as subnet for the custom Indy Pool network, default: `10.0.0.0/24`

## `pytest` custom options

- '--gatherlogs': gather node logs for failed tests, default: not set
- '--logsdir PATH': directory name to store node logs, default: `_build/logs`
