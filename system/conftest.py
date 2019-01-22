import pytest
import asyncio
from utils import *


@pytest.fixture(scope='module')
def looper():
    looper = asyncio.get_event_loop()
    yield looper


@pytest.fixture(scope='function')
def simple(looper):
    looper.run_until_complete(pool.set_protocol_version(2))
    pool_handle, _ = looper.run_until_complete(pool_helper())
    wallet_handle, _, _ = looper.run_until_complete(wallet_helper())
    yield pool_handle, wallet_handle
