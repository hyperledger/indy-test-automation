# Docker Routine

## Dockerfiles

### Client

The [Dockerfile](client/Dockerfile) describes system tests environment.

#### Arguments

- `PYTHON3_VERSION`: version of the python3 to install.
- `LIBINDY_REPO_COMPONENT`: Indy SDK debian repo component.
- `LIBINDY_VERSION`: version of the libindy library.
- `LIBSOVTOKEN_INSTALL`: should be set to `yes` to trigger `libsovtoken` installation.
- `LIBSOVTOKEN_VERSION`: version of the libsovtoken library to install.

### Node

The [Dockerfile](node/Dockerfile) describes environment of nodes inside a pool as a counterpart for system tests.

#### Arguments

- `NODE_REPO_COMPONENT`: Indy Node debian repo component.
- `LIBINDY_CRYPTO_VERSION`: version of the Indy Node debian package.
- `PYTHON3_LIBINDY_CRYPTO_VERSION`: version of the Indy Node debian package.
- `INDY_PLENUM_VERSION`: version of the Indy Node debian package.
- `INDY_NODE_VERSION`: version of the Indy Node debian package.
- `TOKEN_PLUGINS_INSTALL`: should be set to `yes` to trigger installation of `sovrin` with `sovtoken` and `sovtokenfees`.
- `SOVRIN_VERSION`: version of the `sovtoken` plugin.
- `SOVTOKEN_VERSION`: version of the `sovtoken` plugin.
- `SOVTOKENFEES_VERSION`: version of the `sovtokenfees` plugin.

### Images Builder (docker-compose)

The [Dockerfile](docker-compose/Dockerfile) allows to use in-docker docker-compose to build client and node images.

## Scripts

The following scripts automate build/run/clean routine.

Use [prepare.sh](prepare.sh) to prepare docker environment, [run.sh](run.sh) to run test targets and [clean.sh](clean.sh) for a cleanup.

Each script provides a short help, use `--help` for the details.

### [prepare.sh](prepare.sh)

- Builds docker images for client and node passing arguments expected by them as enviroment variables.
- Creates user-defined docker bridge network for system tests.

### [run.sh](run.sh)

- Runs `pytest` inside client docker container.
- Might be run in debug mode by setting the environment variable `INDY_SYSTEM_TESTS_MODE=debug`: docker client container would be run in interactive mode with the environment ready run tests.

### [clean.sh](clean.sh)

- Removes all containers attached to test network and the network itself.

### [docker-compose.yml](docker-compose.yml)

- A `docker-compose` spec to automate docker images build process.

### Examples

Prepare docker environment

```bash
./prepare.sh
```

Prepare docker environment for specific versions of packages

```bash
CLIENT_REPO_COMPONENT=stable NODE_REPO_COMPONENT=stable URSA_VERSION="0.3.2-2" INDY_NODE_VERSION=1.12.4 INDY_PLENUM_VERSION=1.12.4 LIBINDY_REPO_COMPONENT=stable LIBINDY_VERSION="1.13.0~1420" PYTHON3_PYZMQ_VERSION=18.1.0 ./prepare.sh
```

```
DIND_CONTAINER_REGISTRY=docker.io/teracy DIND_IMAGE_NAME=ubuntu:16.04-dind-latest  CLIENT_REPO_COMPONENT=stable NODE_REPO_COMPONENT=stable URSA_VERSION="0.3.2-2" INDY_NODE_VERSION=1.12.4 INDY_PLENUM_VERSION=1.12.4 LIBINDY_REPO_COMPONENT=stable LIBINDY_VERSION="1.13.0~1420" PYTHON3_PYZMQ_VERSION=18.1.0 ./prepare.sh
```

> Note: Not supported anymore
Prepare docker environment with plugins installed

```bash
LIBSOVTOKEN_INSTALL=yes TOKEN_PLUGINS_INSTALL=yes ./prepare.sh
```

Collect tests for some test target

```bash
./run.sh system/indy-node-tests --collect-only
```

Run some test target with specific pytest arguments

```bash
./run.sh system/indy-node-tests/test_ledger.py "-l -v --junit-xml=report.xml -k test_send_and_get_nym_positive"
```

Run with live logs enabled (please check [pytest docs](https://docs.pytest.org/en/3.6.4/logging.html) for more info)

```bash
./run.sh system/indy-node-tests "--log-cli-level 0"
```

Clean all related docker resources

```bash
./clean.sh
```

## Requirements

- `bash`
- `docker` `17.09.0+`
