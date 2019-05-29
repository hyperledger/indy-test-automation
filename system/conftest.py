import pytest
import asyncio
from async_generator import async_generator, yield_

from indy import pool

from .utils import pool_helper, wallet_helper, default_trustee
from .helper import docker_setup_and_teardown as _docker_setup_and_teardown


@pytest.fixture(scope='session')
def event_loop():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pool.set_protocol_version(2))
    yield loop
    loop.close()


@pytest.fixture()
@async_generator
async def pool_handler(event_loop):
    pool_handle, _ = await pool_helper()
    await yield_(pool_handle)


@pytest.fixture()
@async_generator
async def wallet_handler(event_loop):
    wallet_handle, _, _ = await wallet_helper()
    await yield_(wallet_handle)


@pytest.fixture()
@async_generator
async def get_default_trustee(wallet_handler):
    trustee_did, trustee_vk = await default_trustee(wallet_handler)
    await yield_((trustee_did, trustee_vk))


@pytest.fixture(scope='function')
@async_generator
async def docker_setup_and_teardown():
    await _docker_setup_and_teardown()
