# Docker Routine

## Dockerfiles

### Client

The [Dockerfile.ubuntu-1604](client/Dockerfile.ubuntu-1604) describes system tests environment for Hyperledger Indy based on Ubuntu 16.04.
The [Dockerfile.ubuntu-2004](client/Dockerfile.ubuntu-2004) describes system tests environment for Hyperledger Indy based on Ubuntu 20.04.

#### Arguments

- `CLIENT_SOVRIN_REPO_COMPONENT`: Indy SDK debian repo component.
- `LIBINDY_CRYPTO_VERSION`: version of the libindy library.
- `DIND_CONTAINER_REGISTRY`: Container registry of DIND image (needed for GHA)
- `DIND_IMAGE_NAME`: name of the DIND container image
- `UBUNTU_VERSION`: version of Ubuntu (16.04 or 20.04)


### Node

The [Dockerfile.ubuntu-1604](node/Dockerfile.ubuntu-1604) describes environment of nodes inside a pool as a counterpart for system tests for Hyperledger Indy based on Ubuntu 16.04.
The [Dockerfile.ubuntu-2004](node/Dockerfile.ubuntu-2004) describes environment of nodes inside a pool as a counterpart for system tests for Hyperledger Indy based on Ubuntu 20.04.

#### Arguments

- `NODE_REPO_COMPONENT`: Indy Node debian repo component (Hyperledger Artifactory).
- `NODE_SOVRIN_REPO_COMPONENT`: Sovrin repo component
- `INDY_PLENUM_VERSION`: version of the Indy Node debian package.
- `INDY_NODE_VERSION`: version of the Indy Node debian package.
- `PYTHON3_PYZMQ_VERSION`: version of pyzmq
- `UBUNTU_VERSION`: version of Ubuntu (16.04 or 20.04)
- `URSA_VERSION`: version of Ursa debian package


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

Prepare docker environment for specific versions of packages

1. Build Docker-in-Docker (DinD) Image
```bash
### Clone teracyhq/docker-files
git clone git@github.com:teracyhq/docker-files.git teracy-docker-files

### Build DinD - Ubuntu 16.04
cd ./ubuntu/base
docker build -t teracy/ubuntu:16.04-dind-latest --build-arg UBUNTU_VERSION=16.04 .

### Build DinD - Ubuntu 20.04
cd ./ubuntu/base
docker build -t teracy/ubuntu:20.04-dind-latest --build-arg UBUNTU_VERSION=20.04 .
```

2. Prepare Indy-Test-Automation
```bash
### Ubuntu 16.04
DIND_CONTAINER_REGISTRY=teracy DIND_IMAGE_NAME=ubuntu:16.04-dind-latest CLIENT_SOVRIN_REPO_COMPONENT=master NODE_REPO_COMPONENT=main NODE_SOVRIN_REPO_COMPONENT=master INDY_NODE_VERSION="1.13.0~dev197" INDY_PLENUM_VERSION="1.13.0~dev169" URSA_VERSION="0.3.2-2" PYTHON3_PYZMQ_VERSION="18.1.0" LIBINDY_VERSION="1.15.0~1625-xenial" UBUNTU_VERSION="ubuntu-1604" ./prepare.sh

### Ubuntu 20.04
DIND_CONTAINER_REGISTRY=teracy DIND_IMAGE_NAME=ubuntu:20.04-dind-latest CLIENT_SOVRIN_REPO_COMPONENT=master NODE_REPO_COMPONENT=dev NODE_SOVRIN_REPO_COMPONENT=master INDY_NODE_VERSION="1.13.0~dev5" INDY_PLENUM_VERSION="1.13.0~dev175" LIBINDY_VERSION="1.15.0~1625-bionic" URSA_VERSION="0.3.2-1" PYTHON3_PYZMQ_VERSION="18.1.0" UBUNTU_VERSION="ubuntu-2004" ./prepare.sh
```

Collect tests for some test target

```bash
### Ubuntu 16.04
UBUNTU_VERSION="ubuntu-1604" ./run.sh system/indy-node-tests --collect-only

### Ubuntu 20.04
UBUNTU_VERSION="ubuntu-2004" ./run.sh system/indy-node-tests --collect-only
```

Run some test target with specific pytest arguments

```bash
### Ubuntu 16.04
UBUNTU_VERSION="ubuntu-1604" ./run.sh system_node_only/indy-node-tests/test_ledger.py "-l -v --junit-xml=test_ledger-report.xml -k test_send_and_get_nym_positive"

### Ubuntu 20.04
UBUNTU_VERSION="ubuntu-2004" ./run.sh system_node_only/indy-node-tests/test_ledger.py "-l -v --junit-xml=test_ledger-report.xml --log-cli-level 0"
```

Run with live logs enabled (please check [pytest docs](https://docs.pytest.org/en/3.6.4/logging.html) for more info)

```bash
### Ubuntu 16.04
UBUNTU_VERSION="ubuntu-1604" ./run.sh system/indy-node-tests "--log-cli-level 0"

### Ubuntu 20.04
UBUNTU_VERSION="ubuntu-2004" ./run.sh system/indy-node-tests "--log-cli-level 0"
```

Clean all related docker resources

```bash
./clean.sh
```
### GitHub Actions
To run the tests in GitHub Actions pipeline, additional envs have to be set to run the tests.
```bash
### Ubuntu 16.04
UBUNTU_VERSION="${{ env.INPUT_UBUNTUVERSION }}" IMAGE_REPOSITORY="ghcr.io/${{ env.GITHUB_REPOSITORY_NAME }}/" CLIENT_IMAGE="client:${{ env.INPUT_UBUNTUVERSION }}" NODE_IMAGE="node-${{ env.INPUT_UBUNTUVERSION }}" ./run.sh system_node_only/indy-node-tests/test_ledger.py "-l -v --junit-xml=test_ledger-report.xml -k test_send_and_get_nym_positive"

### Ubuntu 20.04
UBUNTU_VERSION="${{ env.INPUT_UBUNTUVERSION }}" IMAGE_REPOSITORY="ghcr.io/${{ env.GITHUB_REPOSITORY_NAME }}/" CLIENT_IMAGE="client:${{ env.INPUT_UBUNTUVERSION }}" NODE_IMAGE="node-${{ env.INPUT_UBUNTUVERSION }}" ./run.sh system_node_only/indy-node-tests/test_ledger.py "-l -v --junit-xml=test_ledger-report.xml -k test_send_and_get_nym_positive"
```

## Requirements

- `bash`
- `docker` `20.10.07`
