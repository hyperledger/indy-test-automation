# Docker Routine

## Dockerfiles

### Client

The [Dockerfile](client/Dockerfile) describes system tests environment.

#### Environment variables

- `PYTHON3_VERSION`: version of the python3 to install, default: `3.5`.
- `LIBINDY_REPO_COMPONENT`: Indy SDK debian repo component, default: `master`.
- `LIBINDY_VERISION`: version of the libindy library, default: `1.8.3~1099`.
- `LIBSOVTOKEN_VERSION`: version of the libsovtoken library to install, default: `0.9.7~66`.

### Node

The [Dockerfile](node/Dockerfile) describes environment of nodes inside a pool as a counterpart for system tests.

#### Environment variables

- `INDY_NODE_REPO_COMPONENT`: Indy Node debian repo component, default: `master`.
- `LIBINDY_CRYPTO_VERSION`: version of the Indy Node debian package, default: `0.4.5`.
- `PYTHON3_LIBINDY_CRYPTO_VERSION`: version of the Indy Node debian package, default: `0.4.5`.
- `INDY_PLENUM_VERSION`: version of the Indy Node debian package, default: `1.8.0~dev802`.
- `INDY_NODE_VERSION`: version of the Indy Node debian package, default: `1.8.0~dev975`.
- `SOVTOKEN_VERSION`: version of the `sovtoken` plugin, default: `0.9.12~37`.
- `SOVTOKENFEES_VERSION`: version of the `sovtokenfees` plugin, default: equal to `sovtoken` version.

### Images Builder (docker-compose)

The [Dockerfile](docker-compose/Dockerfile) allows to use in-docker docker-compose to build client and node images.

## Scripts

The following scripts automate build/run/clean routine.

Use [prepare.sh](prepare.sh) to prepare docker environment, [run.sh](run.sh) to run test targets and [clean.sh](clean.sh) for a cleanup.

Each script provides a short help, use `--help` for the details.

### [prepare.sh](prepare.sh)

- Builds docker images for client and node passing env variables expected by them.
- Creates user-defined docker bridge network for system tests.

### [run.sh](run.sh)

- Runs `pytest` inside client docker container.

### [clean.sh](clean.sh)

- Removes all containers attached to test network and the network itself.

### [docker-compose.yml](docker-compose.yml)

- A `docker-compose` spec to automate docker images build process.

### Examples

Prepare docker environment

```bash
./prepare.sh
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
