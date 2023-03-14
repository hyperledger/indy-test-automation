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
# use the same did with different roles to ADD and EDIT since adder did is a part of unique revoc reg def id
async def test_case_revoc_reg_def(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
        adder_role, adder_role_num, editor_role, editor_role_num):
    trustee_did, _ = get_default_trustee
    # add adder to add revoc reg def
    adder_did, adder_vk = await create_and_store_did(wallet_handler)
    res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
    assert res['txnMetadata']['seqNo'] is not None
    schema_id, _ = await send_schema(
        pool_handler, wallet_handler, trustee_did, 'schema1', '1.0', json.dumps(['age', 'sex', 'height', 'name'])
    )
    await asyncio.sleep(1)
    res = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
    schema_id, schema_json = parse_get_schema_response(res)
    cred_def_id, _, res = await send_cred_def(
        pool_handler, wallet_handler, trustee_did, schema_json, 'cred_def_tag', None,
        support_revocation=True)
    # set rule for adding
    req = ledger.build_auth_rule_request(trustee_did, '113', 'ADD', '*', None, '*',
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
    req = ledger.build_auth_rule_request(trustee_did, '113', 'EDIT', '*', '*', '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': editor_role_num,
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res3 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    assert res3['txnMetadata']['seqNo'] is not None
    # add revoc reg def
    # tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
    # tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
    revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = await create_and_store_revoc_reg(
        wallet_handler, adder_did, 'CL_ACCUM', 'TAG1', cred_def_id,
            max_cred_num=1, issuance_type='ISSUANCE_BY_DEFAULT') 
    request1 = ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
    res4 = await sign_and_submit_request(pool_handler, wallet_handler, adder_did, request1)
    assert res4['txnMetadata']['seqNo'] is not None
    if adder_role != editor_role:
        # try to edit revoc reg def as adder - should be rejected
        revoc_reg_def_json = json.loads(revoc_reg_def_json)
        revoc_reg_def_json['value']['tailsHash'] = random_string(30)
        revoc_reg_def_json = json.dumps(revoc_reg_def_json)
        request2 = ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
        with pytest.raises(VdrError) as exp_err:
            await sign_and_submit_request(pool_handler, wallet_handler, adder_did, request2)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # change adder role to edit revoc reg def
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, None, None, editor_role)
        assert res['txnMetadata']['seqNo'] is not None
    # edit revoc reg def
    revoc_reg_def_json = json.loads(revoc_reg_def_json)
    revoc_reg_def_json['value']['tailsHash'] = random_string(20)
    revoc_reg_def_json = json.dumps(revoc_reg_def_json)
    request3 = ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
    res5 = await sign_and_submit_request(pool_handler, wallet_handler, adder_did, request3)
    assert res5['txnMetadata']['seqNo'] is not None
    if adder_role != editor_role:
        # try to add another revoc reg def as editor - should be rejected
        revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = await create_and_store_revoc_reg(
            wallet_handler, adder_did, 'CL_ACCUM', 'TAG2', cred_def_id,
                max_cred_num=2, issuance_type='ISSUANCE_BY_DEFAULT') 
        request = ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
        with pytest.raises(VdrError) as exp_err:
            await sign_and_submit_request(pool_handler, wallet_handler, adder_did, request)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
