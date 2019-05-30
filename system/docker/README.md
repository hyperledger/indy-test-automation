# System Tests Dockerfiles

## Client

The [Dockerfile](client/Dockerfile) describes system tests environment.

### Environment variables

- `PYTHON3_VERSION`: version of the python3 to install, default: `3.5`.
- `LIBINDY_REPO_COMPONENT`: Indy SDK debian repo component, default: `master`.
- `LIBINDY_VERISION`: version of the libindy library, default: `1.8.3~1099`.
- `LIBSOVTOKEN_VERSION`: version of the libsovtoken library to install, default: `0.9.7~66`.

## Node

The [Dockerfile](node/Dockerfile) describes environment of nodes inside a pool as a counterpart for system tests.

### Environment variables

- `INDY_NODE_REPO_COMPONENT`: Indy Node debian repo component, default: `master`.
- `LIBINDY_CRYPTO_VERSION`: version of the Indy Node debian package, default: `0.4.5`.
- `PYTHON3_LIBINDY_CRYPTO_VERSION`: version of the Indy Node debian package, default: `0.4.5`.
- `INDY_PLENUM_VERSION`: version of the Indy Node debian package, default: `1.8.0~dev802`.
- `INDY_NODE_VERSION`: version of the Indy Node debian package, default: `1.8.0~dev975`.
- `SOVTOKEN_VERSION`: version of the `sovtoken` plugin, default: `0.9.12~37`.
- `SOVTOKENFEES_VERSION`: version of the `sovtokenfees` plugin, default: equal to `sovtoken` version.

## Images Builder (docker-compose)

The [Dockerfile](docker-compose/Dockerfile) allows to use in-docker docker-compose to build client and node images.

# Scripts

## [prepare.sh](prepare.sh)

- Builds docker images for client and node passing env variables expected by them.
- Creates user-defined docker bridge network for system tests.

## [clean.sh](clean.sh)

- Removes all containers attached to test network and the network itself.

## [run.sh](run.sh)

- Calls [prepare.sh](prepare.sh) to build environment for system tests.
- Runs pytest inside client docker container.

## [docker-compose.yml](docker-compose.yml)

- A spec to automate docker images build process.

# Requirements

- `docker` `17.09.0+`
