import pytest
import asyncio
from system.utils import *
from aries_askar.error import AskarError, AskarErrorCode


import logging
logger = logging.getLogger(__name__)


@pytest.mark.parametrize('adder_role, adder_role_num', [
    ('TRUSTEE', '0'),
    ('STEWARD', '2'),
    ('TRUST_ANCHOR', '101'),
    ('NETWORK_MONITOR', '201')
])
@pytest.mark.asyncio
async def test_case_schema(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, adder_role, adder_role_num
):  # we can add schema only
    trustee_did, _ = get_default_trustee
    # add adder to add schema
    adder_did, adder_vk = await create_and_store_did(wallet_handler)
    res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
    assert res['txnMetadata']['seqNo'] is not None
    # set rule for adding
    req = ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': adder_role_num,
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    print(res2)
    assert res2['txnMetadata']['seqNo'] is not None
    # add schema
    res4 = await send_schema(pool_handler, wallet_handler, adder_did, 'schema1', '1.0', json.dumps(['attr1']))
    print(res4)
    assert res4[1]['txnMetadata']['seqNo'] is not None
    # edit schema - nobody can edit schemas - should be rejected
    with pytest.raises(AskarError) as exp_err:
        await send_schema(pool_handler, wallet_handler, adder_did, 'schema1', '1.0', json.dumps(['attr1', 'attr2']))
    assert exp_err.value.code == AskarErrorCode.DUPLICATE
