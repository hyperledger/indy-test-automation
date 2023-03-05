import pytest
import time
import asyncio
from indy import did, payment
from system.utils import *
import logging

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=0, format='%(asctime)s %(message)s')


@pytest.mark.asyncio
async def test_misc_freshness_vdr(docker_setup_and_teardown, check_no_failures_fixture):
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()

    trustee_did,  trustee_vk  = await create_and_store_did(wallet_handle, seed='000000000000000000000000Trustee1')
    trustee_did2, trustee_vk2 = await create_and_store_did(wallet_handle, seed='000000000000000000000000Trustee2')
    trustee_did3, trustee_vk3 = await create_and_store_did(wallet_handle, seed='000000000000000000000000Trustee3')
    trustee_did4, trustee_vk4 = await create_and_store_did(wallet_handle, seed='000000000000000000000000Trustee4')

    await send_nym(pool_handle, wallet_handle, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
    await send_nym(pool_handle, wallet_handle, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
    await send_nym(pool_handle, wallet_handle, trustee_did, trustee_did4, trustee_vk4, None, 'TRUSTEE')

    new_steward_did, new_steward_vk = await create_and_store_did(wallet_handle)
    some_did = random_did_and_json()[0]
    await send_nym(pool_handle, wallet_handle, trustee_did, new_steward_did, new_steward_vk, 'steward', 'STEWARD')

    # write domain ledger txns
    timestamp0 = int(time.time())
    nym = await send_nym(pool_handle, wallet_handle, trustee_did, some_did)
    attrib = await send_attrib(
        pool_handle, wallet_handle, trustee_did, some_did, None, json.dumps({'key': 'value'}), None
    )
    schema_id, schema = await send_schema(
        pool_handle, wallet_handle, trustee_did, random_string(10), '1.0', json.dumps(["age", "sex", "height", "name"])
    )
    await asyncio.sleep(3)
    temp = await get_schema(pool_handle, wallet_handle, trustee_did, schema_id)
    schema_id, schema_json = parse_get_schema_response(temp)
    cred_def_id, _, cred_def = await send_cred_def(
        pool_handle, wallet_handle, trustee_did, schema_json, random_string(5), 'CL', support_revocation=True)
    revoc_reg_def_id1, _, _, revoc_reg_def = await send_revoc_reg_def(
        pool_handle, wallet_handle, trustee_did, 'CL_ACCUM', random_string(5), cred_def_id,
        max_cred_num=1, issuance_type='ISSUANCE_BY_DEFAULT')
    revoc_reg_def_id2, _, _, revoc_reg_entry = await send_revoc_reg_entry(
        pool_handle, wallet_handle, trustee_did, 'CL_ACCUM', random_string(5), cred_def_id,
            max_cred_num=1, issuance_type='ISSUANCE_BY_DEFAULT')

    timestamp1 = int(time.time())

    await asyncio.sleep(330)

    # read domain ledger txns
    _get_nym = await get_nym(pool_handle, wallet_handle, trustee_did, some_did)
    _get_attrib = await get_attrib(pool_handle, wallet_handle, trustee_did, some_did, None, 'key', None)
    _get_schema = await get_schema(pool_handle, wallet_handle, trustee_did, schema_id)
    _get_cred_def = await get_cred_def(pool_handle, wallet_handle, trustee_did, cred_def_id)
    _get_revoc_reg_def = await get_revoc_reg_def(pool_handle, wallet_handle, trustee_did, revoc_reg_def_id1)
    _get_revoc_reg = await get_revoc_reg(pool_handle, wallet_handle, trustee_did, revoc_reg_def_id2, timestamp1)
    _get_revoc_reg_delta = await get_revoc_reg_delta(
        pool_handle, wallet_handle, trustee_did, revoc_reg_def_id2, timestamp0, timestamp1
    )

    get_results = [
        _get_nym, _get_attrib, _get_schema, _get_cred_def, _get_revoc_reg_def, _get_revoc_reg, _get_revoc_reg_delta
    ]
    for res in get_results:
        assert res['seqNo'] is not None
        assert (int(time.time()) - res['state_proof']['multi_signature']['value']['timestamp']) <= 300