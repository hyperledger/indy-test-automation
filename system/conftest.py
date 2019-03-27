import pytest
from system.utils import *
from indy import *
from async_generator import yield_, async_generator
import os
import subprocess
from subprocess import CalledProcessError


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pool.set_protocol_version(2))
    yield loop
    loop.close()


@pytest.fixture(scope='module')
@async_generator
async def pool_handler(event_loop):
    pool_handle, _ = await pool_helper()
    await yield_(pool_handle)


@pytest.fixture(scope='module')
@async_generator
async def wallet_handler(event_loop):
    wallet_handle, _, _ = await wallet_helper()
    await yield_(wallet_handle)


@pytest.fixture()
@async_generator
async def get_default_trustee(wallet_handler):
    trustee_did, trustee_vk = await default_trustee(wallet_handler)
    await yield_((trustee_did, trustee_vk))


@pytest.fixture()
@async_generator
async def docker_setup_and_teardown():
    os.chdir('/home/indy/indy-node/environment/docker/pool')
    containers = subprocess.check_output(['docker', 'ps', '-a', '-q']).decode().strip().split()
    outputs = [subprocess.check_call(['docker', 'rm', container, '-f']) for container in containers]
    assert outputs is not None
    # Uncomment to destroy all images too
    # images = subprocess.check_output(['docker', 'images', '-q']).decode().strip().split()
    # try:
    #     outputs = [subprocess.check_call(['docker', 'rmi', image, '-f']) for image in images]
    #     assert outputs is not None
    # except CalledProcessError:
    #     pass
    pool_start_result = subprocess.check_output(['./pool_start.sh', '7']).decode().strip()
    assert pool_start_result.find('Pool started') is not -1
    time.sleep(15)

    await yield_()

    containers = subprocess.check_output(['docker', 'ps', '-a', '-q']).decode().strip().split()
    outputs = [subprocess.check_call(['docker', 'rm', container, '-f']) for container in containers]
    assert outputs is not None
    # Uncomment to destroy all images too
    # images = subprocess.check_output(['docker', 'images', '-q']).decode().strip().split()
    # try:
    #     outputs = [subprocess.check_call(['docker', 'rmi', image, '-f']) for image in images]
    #     assert outputs is not None
    # except CalledProcessError:
    #     pass
    os.chdir('~')
