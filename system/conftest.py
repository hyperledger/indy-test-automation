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


@pytest.fixture()
@async_generator
async def initial_token_minting(pool_handler, wallet_handler, get_default_trustee):
    await payment_initializer('libsovtoken.so', 'sovtoken_init')
    libsovtoken_payment_method = 'sov'
    trustee_did, _ = get_default_trustee
    address = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps(
        {"seed": str('0000000000000000000000000Wallet0')}))
    trustee_did_second, trustee_vk_second = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    trustee_did_third, trustee_vk_third = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_second, trustee_vk_second, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_third, trustee_vk_third, None, 'TRUSTEE')
    req, _ = await payment.build_mint_req(wallet_handler, trustee_did,
                                          json.dumps([{'recipient': address, 'amount': 1000 * 100000}]), None)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_second, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_third, req)
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    await yield_(address)


@pytest.fixture()
@async_generator
async def initial_fees_setting(pool_handler, wallet_handler, get_default_trustee):
    await payment_initializer('libsovtoken.so', 'sovtoken_init')
    libsovtoken_payment_method = 'sov'
    trustee_did, _ = get_default_trustee
    trustee_did_second, trustee_vk_second = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    trustee_did_third, trustee_vk_third = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_second, trustee_vk_second, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_third, trustee_vk_third, None, 'TRUSTEE')
    fees = {'trustee_0': 0 * 100000,
            'steward_0': 0 * 100000,
            'trust_anchor_0': 0 * 100000,
            'network_monitor_0': 0 * 100000,
            'add_identity_owner_50': 50 * 100000,
            'edit_identity_owner_0': 0 * 100000,
            'add_schema_250': 250 * 100000,
            'add_cred_def_125': 125 * 100000,
            'add_rrd_100': 100 * 100000,
            'add_rre_0_5': int(0.5 * 100000)
            }
    req = await payment.build_set_txn_fees_req(wallet_handler, trustee_did, libsovtoken_payment_method,
                                               json.dumps(fees))
    req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_second, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_third, req)
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    await yield_(fees)


@pytest.fixture(scope='function')
@async_generator
async def docker_setup_and_teardown():
    await _docker_setup_and_teardown()
