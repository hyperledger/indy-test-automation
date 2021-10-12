import pytest
import asyncio
from system.utils import *


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
    adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
    assert res['op'] == 'REPLY'
    schema_id, _ = await send_schema(
        pool_handler, wallet_handler, trustee_did, 'schema1', '1.0', json.dumps(['age', 'sex', 'height', 'name'])
    )
    await asyncio.sleep(1)
    res = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, _, res = await send_cred_def(
        pool_handler, wallet_handler, trustee_did, schema_json, 'cred_def_tag', None,
        json.dumps({'support_revocation': True})
    )
    # set rule for adding
    req = await ledger.build_auth_rule_request(trustee_did, '113', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': adder_role_num,
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res2)
    assert res2['op'] == 'REPLY'
    # set rule for editing
    req = await ledger.build_auth_rule_request(trustee_did, '113', 'EDIT', '*', '*', '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': editor_role_num,
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res3)
    assert res3['op'] == 'REPLY'
    # add revoc reg def
    tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
    tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
    revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = await anoncreds.issuer_create_and_store_revoc_reg(
        wallet_handler, adder_did, None, 'TAG1', cred_def_id,
        json.dumps({'max_cred_num': 1, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}), tails_writer_handle
    )
    request = await ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
    res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, request))
    print(res4)
    assert res4['op'] == 'REPLY'
    if adder_role != editor_role:
        # try to edit revoc reg def as adder - should be rejected
        _request = json.loads(request)
        _request['operation']['value']['tailsHash'] = random_string(30)
        _request['reqId'] += _request['reqId']
        res5 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, json.dumps(_request))
        )
        print(res5)
        assert res5['op'] == 'REJECT'
        # change adder role to edit revoc reg def
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, None, None, editor_role)
        print(res)
        assert res['op'] == 'REPLY'
    # edit revoc reg def
    request = json.loads(request)
    request['operation']['value']['tailsHash'] = random_string(20)
    request['reqId'] += request['reqId']
    res6 = json.loads(
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, json.dumps(request))
    )
    print(res6)
    assert res6['op'] == 'REPLY'
    if adder_role != editor_role:
        # try to add another revoc reg def as editor - should be rejected
        revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = await anoncreds.issuer_create_and_store_revoc_reg(
            wallet_handler, adder_did, None, 'TAG2', cred_def_id,
            json.dumps({'max_cred_num': 2, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}), tails_writer_handle
        )
        request = await ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
        res7 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, request))
        print(res7)
        assert res7['op'] == 'REJECT'
