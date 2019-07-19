import pytest
import json
import hashlib
import time
import logging
import asyncio
from async_generator import async_generator, yield_

from indy import pool, did, ledger, IndyError

from system.utils import *

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=0, format='%(asctime)s %(message)s')

@pytest.fixture(scope='module', autouse=True)
@async_generator
async def docker_setup_and_teardown(docker_setup_and_teardown_module):
    await yield_()


@pytest.mark.parametrize('writer_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
@pytest.mark.parametrize('reader_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', None])
@pytest.mark.asyncio
async def test_send_and_get_nym_positive(writer_role, reader_role):
    assert False
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    target_did, target_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    writer_did, writer_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    reader_did, reader_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    # Trustee adds NYM writer
    await send_nym(pool_handle, wallet_handle, trustee_did, writer_did, writer_vk, None, writer_role)
    # Trustee adds NYM reader
    await send_nym(pool_handle, wallet_handle, trustee_did, reader_did, reader_vk, None, reader_role)
    # Writer sends NYM
    res1 = await send_nym(pool_handle, wallet_handle, writer_did, target_did)
    # Reader gets NYM
    res2 = await read_eventually_positive(get_nym, pool_handle, wallet_handle, target_did, target_did)

    assert res1['op'] == 'REPLY'
    assert res2['result']['seqNo'] is not None

    print(res1)
    print(res2)



