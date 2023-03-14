import pytest
import asyncio
from system.utils import *

from indy_vdr.error import VdrError, VdrErrorCode

import logging
logger = logging.getLogger(__name__)


@pytest.mark.parametrize('adder_role, adder_role_num', [
    ('TRUSTEE', '0'),
    ('STEWARD', '2'),
    ('TRUST_ANCHOR', '101'),
    ('NETWORK_MONITOR', '201')
])
@pytest.mark.parametrize('editor_role, editor_role_num', [
    ('NETWORK_MONITOR', '201'),
    ('TRUST_ANCHOR', '101'),
    ('STEWARD', '2'),
    ('TRUSTEE', '0')
])
@pytest.mark.asyncio
# use the same did with different roles to ADD and EDIT since adder did is a part of unique cred def id
async def test_case_cred_def(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
        adder_role, adder_role_num, editor_role, editor_role_num):
    trustee_did, _ = get_default_trustee
    # add adder to add cred def
    adder_did, adder_vk = await create_and_store_did(wallet_handler)
    res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
    assert res['txnMetadata']['seqNo'] is not None
    schema_id, _ = await send_schema(pool_handler, wallet_handler, trustee_did,
                                     'schema1', '1.0', json.dumps(["age", "sex", "height", "name"]))
    await asyncio.sleep(1)
    res = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
    schema_id, schema_json = parse_get_schema_response(res)
    # set rule for adding
    req = ledger.build_auth_rule_request(trustee_did, '102', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': adder_role_num,
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    assert res2['txnMetadata']['seqNo'] is not None
    # set rule for editing
    req = ledger.build_auth_rule_request(trustee_did, '102', 'EDIT', '*', '*', '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': editor_role_num,
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res3 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    assert res3['txnMetadata']['seqNo'] is not None
    # add cred def
    cred_def_id, cred_def_json = await create_and_store_cred_def(
        wallet_handler, adder_did, schema_json, 'TAG1', None, support_revocation=False)
    request1 = ledger.build_cred_def_request(adder_did, cred_def_json)
    res4 = await sign_and_submit_request(pool_handler, wallet_handler, adder_did, request1)
    assert res4['txnMetadata']['seqNo'] is not None
    if adder_role != editor_role:
        # try to edit cred def as adder - should be rejected
        cred_def_json = json.loads(cred_def_json)
        cred_def_json['value']['primary']['n'] = '123456789'
        cred_def_json = json.dumps(cred_def_json)
        request2 = ledger.build_cred_def_request(adder_did, cred_def_json)
        with pytest.raises(VdrError) as exp_err:
            await sign_and_submit_request(pool_handler, wallet_handler, adder_did, request2)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # change adder role to edit cred def
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, None, None, editor_role)
        assert res['txnMetadata']['seqNo'] is not None
    # edit cred def
    cred_def_json = json.loads(cred_def_json)
    cred_def_json['value']['primary']['n'] = '123456'
    cred_def_json = json.dumps(cred_def_json)
    request3 = ledger.build_cred_def_request(adder_did, cred_def_json)
    res6 = await sign_and_submit_request(pool_handler, wallet_handler, adder_did, request3)
    assert res6['txnMetadata']['seqNo'] is not None
    if adder_role != editor_role:
        # try to add another cred def as editor - should be rejected
        cred_def_id, cred_def_json = await create_and_store_cred_def(
            wallet_handler, adder_did, schema_json, 'TAG2', None, support_revocation=False)
        request = ledger.build_cred_def_request(adder_did, cred_def_json)
        with pytest.raises(VdrError) as exp_err:
            await sign_and_submit_request(pool_handler, wallet_handler, adder_did, request)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
