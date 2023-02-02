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
async def test_case_nym(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
        adder_role, adder_role_num, editor_role, editor_role_num
):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await create_and_store_did(wallet_handler)
    # add adder to add nym
    adder_did, adder_vk = await create_and_store_did(wallet_handler)
    res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
    assert res['txnMetadata']['seqNo'] is not None
    # add editor to edit nym
    editor_did, editor_vk = await create_and_store_did(wallet_handler)
    res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
    assert res['txnMetadata']['seqNo'] is not None
    req = ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': adder_role_num,
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    assert res2['txnMetadata']['seqNo'] is not None
    req = ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'verkey', '*', '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': editor_role_num,
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res3 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    assert res3['txnMetadata']['seqNo'] is not None
    # add nym with verkey by adder
    res4 = await send_nym(pool_handler, wallet_handler, adder_did, new_did, adder_vk)  # push adder vk
    assert res4['txnMetadata']['seqNo'] is not None
    # edit verkey by editor
    res5 = await send_nym(pool_handler, wallet_handler, editor_did, new_did, editor_vk)  # push editor vk
    assert res5['txnMetadata']['seqNo'] is not None
    # negative cases
    if adder_role != editor_role:
        # try to add another nym with editor did - should be rejected
        with pytest.raises(VdrError) as exp_err:
            await send_nym(pool_handler, wallet_handler, editor_did, random_did_and_json()[0])
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # try to edit initial nym one more time with adder did - should be rejected
        with pytest.raises(VdrError) as exp_err:
            await send_nym(pool_handler, wallet_handler, adder_did, new_did, adder_vk)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
