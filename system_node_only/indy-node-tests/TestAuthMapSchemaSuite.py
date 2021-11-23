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
@pytest.mark.asyncio
async def test_case_schema(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, adder_role, adder_role_num
):  # we can add schema only
    trustee_did, _ = get_default_trustee
    # add adder to add schema
    adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
    assert res['op'] == 'REPLY'
    # set rule for adding
    req = await ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
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
    # add schema
    res4 = await send_schema(pool_handler, wallet_handler, adder_did, 'schema1', '1.0', json.dumps(['attr1']))
    print(res4)
    assert res4[1]['op'] == 'REPLY'
    # edit schema - nobody can edit schemas - should be rejected
    res5 = await send_schema(pool_handler, wallet_handler, adder_did, 'schema1', '1.0', json.dumps(['attr1', 'attr2']))
    print(res5)
    assert res5[1]['op'] == 'REJECT'
