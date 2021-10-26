import pytest
import asyncio
from system.utils import *


@pytest.mark.asyncio
async def test_off_ledger_signature(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    # libsovtoken_payment_method = 'sov'
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    other_did, other_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    trustee_did_second, trustee_vk_second = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    trustee_did_third, trustee_vk_third = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_second, trustee_vk_second, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_third, trustee_vk_third, None, 'TRUSTEE')
    # address = initial_token_minting
    # fees = {'off_ledger_nym': 100 * 100000}
    # req = await payment.build_set_txn_fees_req(
    # #     wallet_handler, trustee_did, libsovtoken_payment_method, json.dumps(fees)
    # # )
    # req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
    # req = await ledger.multi_sign_request(wallet_handler, trustee_did_second, req)
    # req = await ledger.multi_sign_request(wallet_handler, trustee_did_third, req)
    # res = json.loads(await ledger.submit_request(pool_handler, req))
    # assert res['op'] == 'REPLY'
    req0 = await ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
                                                json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': '*',
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'off_ledger_signature': True,
                                                   'metadata': {}
                                                }))
    res0 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req0))
    print(res0)
    assert res0['op'] == 'REPLY'
    req1 = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '',
                                                json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': '0',
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'off_ledger_signature': True,
                                                   'metadata': {}
                                                }))
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req1))
    print(res1)
    assert res1['op'] == 'REQNACK'
    req2 = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '',
                                                json.dumps({
                                                    'constraint_id': 'OR',
                                                    'auth_constraints': [
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '0',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '*',
                                                               'sig_count': 0,
                                                               'need_to_be_owner': False,
                                                               'off_ledger_signature': True,
                                                               'metadata': {}
                                                           }
                                                    ]
                                                }))
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req2))
    print(res2)
    assert res2['op'] == 'REPLY'
    res3 = await send_nym(pool_handler, wallet_handler, new_did, other_did, other_vk, 'not my own nym', None)
    print(res3)
    assert res3['op'] == 'REQNACK'
    res4 = await send_schema(pool_handler, wallet_handler, new_did, 'schema', '1.0', json.dumps(['attr']))
    print(res4)
    assert res4[1]['op'] == 'REQNACK'
    # req, _ = await payment.build_get_payment_sources_request(wallet_handler, new_did, address)
    # res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, new_did, req)
    # source = json.loads(await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res))[0]['source']
    # req5 = await ledger.build_nym_request(new_did, new_did, new_vk, 'my own did', None)
    # req5, _ = await payment.add_request_fees(
    #     wallet_handler, new_did, req5, json.dumps([source]), json.dumps(
    #         [{'recipient': address, 'amount': 900 * 100000}]
    #     ), None
    # )
    # res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, new_did, req5))
    # print(res5)
    # assert res5['op'] == 'REPLY'
    req = await ledger.build_get_auth_rule_request(None, None, None, None, None, None)
    res6 = json.loads(await ledger.submit_request(pool_handler, req))
    assert res6['op'] == 'REPLY'
    print(res6)
