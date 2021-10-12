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
async def test_case_attrib(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
        adder_role, adder_role_num, editor_role, editor_role_num
):
    trustee_did, _ = get_default_trustee
    # add target nym
    target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(pool_handler, wallet_handler, trustee_did, target_did, target_vk)
    assert res['op'] == 'REPLY'
    # add adder to add attrib
    adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
    assert res['op'] == 'REPLY'
    # add editor to edit attrib
    editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
    assert res['op'] == 'REPLY'
    # set rule for adding
    req = await ledger.build_auth_rule_request(trustee_did, '100', 'ADD', '*', None, '*',
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
    req = await ledger.build_auth_rule_request(trustee_did, '100', 'EDIT', '*', '*', '*',
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
    # add attrib for target did by non-owner adder
    res4 = await send_attrib(
        pool_handler, wallet_handler, adder_did, target_did, None, json.dumps({'key1': 'value1'}), None
    )
    print(res4)
    assert res4['op'] == 'REPLY'
    # edit attrib for target did by non-owner editor
    res5 = await send_attrib(
        pool_handler, wallet_handler, editor_did, target_did, None, json.dumps({'key1': 'value2'}), None
    )
    print(res5)
    assert res5['op'] == 'REPLY'
    # negative cases
    if adder_role != editor_role:
        # try to add another attrib with editor did - should be rejected
        res6 = await send_attrib(
            pool_handler, wallet_handler, editor_did, target_did, None, json.dumps({'key2': 'value1'}), None
        )
        print(res6)
        assert res6['op'] == 'REJECT'
        # try to edit initial attrib one more time with adder did - should be rejected
        res7 = await send_attrib(
            pool_handler, wallet_handler, adder_did, target_did, None, json.dumps({'key1': 'value3'}), None
        )
        print(res7)
        assert res7['op'] == 'REJECT'
