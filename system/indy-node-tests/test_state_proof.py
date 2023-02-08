import pytest
import asyncio
from random import randrange as rr
from system.utils import *


@pytest.mark.parametrize('wait_time', [0, 660])  # 0 - common proof reading, 660 - freshness proof reading
@pytest.mark.asyncio
async def test_misc_state_proof(
        docker_setup_and_teardown, payment_init, pool_handler, wallet_handler, get_default_trustee,
        initial_token_minting, initial_fees_setting, nodes_num, wait_time, check_no_failures_fixture
):
    libsovtoken_payment_method = 'sov'
    trustee_did, _ = get_default_trustee
    steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    random_did = random_did_and_json()[0]
    address = initial_token_minting
    address2 = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, '{}')

    # write all txn types to the ledger
    await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, 'STEWARD')
    req = await ledger.build_node_request(
        steward_did, steward_vk, json.dumps(
            {
                'alias': random_string(5),
                'client_ip': '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                'client_port': rr(1, 32767),
                'node_ip': '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                'node_port': rr(1, 32767),
                'services': []
            }
        )
    )
    res_node = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req))
    assert res_node['op'] == 'REPLY'

    req = await ledger.build_auth_rule_request(
        trustee_did, '118', 'ADD', 'action', '*', '*', json.dumps(
            {
               'constraint_id': 'ROLE',
               'role': '*',
               'sig_count': 10,
               'need_to_be_owner': False,
               'metadata': {}
            }
        )
    )
    res_auth = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res_auth['op'] == 'REPLY'

    res_nym = await send_nym(pool_handler, wallet_handler, trustee_did, random_did)
    assert res_nym['op'] == 'REPLY'

    res_attr = await send_attrib(
        pool_handler, wallet_handler, trustee_did, random_did, None, json.dumps({'key': 'value'}), None
    )
    assert res_attr['op'] == 'REPLY'

    schema_id, res_sch = await send_schema(
        pool_handler, wallet_handler, trustee_did, random_string(10), '1.0', json.dumps(
            [random_string(1), random_string(2), random_string(3)]
        )
    )
    assert res_sch['op'] == 'REPLY'

    await asyncio.sleep(5)

    res = json.dumps(await get_schema(pool_handler, wallet_handler, trustee_did, schema_id))
    schema_id, schema_json = await ledger.parse_get_schema_response(res)
    cred_def_id, _, res_cred_def = await send_cred_def(
        pool_handler, wallet_handler, trustee_did, schema_json, random_string(3), None, json.dumps(
            {'support_revocation': True}
        )
    )
    assert res_cred_def['op'] == 'REPLY'

    timestamp0 = int(time.time())

    revoc_reg_def_id, _, _, res_entry = await send_revoc_reg_entry(
        pool_handler, wallet_handler, trustee_did, 'CL_ACCUM', random_string(3), cred_def_id, json.dumps(
            {'max_cred_num': 1, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}
        )
    )
    assert res_entry['op'] == 'REPLY'

    req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address)
    res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    source = json.loads(
        await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res)
    )[0]['source']
    req, _ = await payment.build_payment_req(
        wallet_handler, trustee_did, json.dumps([source]), json.dumps(
            [{"recipient": address2, "amount": 1000 * 100000}]
        ), None
    )
    res_pay = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    assert json.loads(res_pay)['op'] == 'REPLY'
    receipts = json.loads(await payment.parse_payment_response(libsovtoken_payment_method, res_pay))
    receipt = receipts[0]

    # set fees
    print(initial_fees_setting)

    # set auth rule for schema
    req = await ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
                                               json.dumps({
                                                           'constraint_id': 'ROLE',
                                                           'role': '0',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'add_schema_250'}
                                                        }
                                                    )
                                               )
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res1['op'] == 'REPLY'

    # write schema with fees as the last txn
    source2, _ = await get_payment_sources(pool_handler, wallet_handler, address2)
    schema_id, schema_json = await anoncreds.issuer_create_schema(
        trustee_did, random_string(5), '1.0', json.dumps(['name', 'age'])
    )
    req = await ledger.build_schema_request(trustee_did, schema_json)
    req_with_fees_json, _ = await payment.add_request_fees(
        wallet_handler, trustee_did, req, json.dumps([source2]), json.dumps(
            [{'recipient': address2, 'amount': 750 * 100000}]
        ), None
    )
    res2 = json.loads(
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req_with_fees_json)
    )
    assert res2['op'] == 'REPLY'

    req = await ledger.build_acceptance_mechanisms_request(
        trustee_did, json.dumps({'aml_key': 'AML text'}), 'AML version', None
    )
    res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res3['op'] == 'REPLY'
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, 'TAA text', 'TAA version', ratification_ts=int(time.time())
    )
    res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res4['op'] == 'REPLY'

    # txns must be written at ALL nodes before they will be stopped
    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

    await asyncio.sleep(wait_time)

    # stop all nodes except one
    hosts = [NodeHost(i) for i in range(1, nodes_num+1)]
    print([host.stop_service() for host in hosts[:-1]])

    # read all txns written from the single node
    timestamp1 = int(time.time())

    req1 = await ledger.build_get_nym_request(None, random_did)
    res1 = json.loads(await ledger.submit_request(pool_handler, req1))
    assert res1['result']['seqNo'] is not None

    req2 = await ledger.build_get_attrib_request(None, random_did, 'key', None, None)
    res2 = json.loads(await ledger.submit_request(pool_handler, req2))
    assert res2['result']['seqNo'] is not None

    req3 = await ledger.build_get_schema_request(None, schema_id)
    res3 = json.loads(await ledger.submit_request(pool_handler, req3))
    assert res3['result']['seqNo'] is not None

    req4 = await ledger.build_get_cred_def_request(None, cred_def_id)
    res4 = json.loads(await ledger.submit_request(pool_handler, req4))
    assert res4['result']['seqNo'] is not None

    req5 = await ledger.build_get_revoc_reg_def_request(None, revoc_reg_def_id)
    res5 = json.loads(await ledger.submit_request(pool_handler, req5))
    assert res5['result']['seqNo'] is not None

    # consensus is impossible with timestamp0 here! IS-1263
    req6 = await ledger.build_get_revoc_reg_request(None, revoc_reg_def_id, timestamp1)
    res6 = json.loads(await ledger.submit_request(pool_handler, req6))
    assert res6['result']['seqNo'] is not None

    req66 = await ledger.build_get_revoc_reg_request(None, revoc_reg_def_id, timestamp0)
    res66 = json.loads(await ledger.submit_request(pool_handler, req66))
    assert res66['result']['seqNo'] is None

    # consensus is impossible with (timestamp0, timestamp1) here! IS-1264
    req7 = await ledger.build_get_revoc_reg_delta_request(None, revoc_reg_def_id, timestamp0, timestamp1)
    res7 = json.loads(await ledger.submit_request(pool_handler, req7))
    assert res7['result']['seqNo'] is not None

    for ledger_type, seqno in [('DOMAIN', 16), ('POOL', 8), ('CONFIG', 1), ('1001', 1)]:
        req8 = await ledger.build_get_txn_request(None, ledger_type, seqno)
        res8 = json.loads(await ledger.submit_request(pool_handler, req8))
        assert res8['result']['seqNo'] is not None

    req9, _ = await payment.build_get_payment_sources_request(wallet_handler, None, address2)
    res9 = json.loads(await ledger.submit_request(pool_handler, req9))
    assert res9['op'] == 'REPLY' and res9['result']['outputs'][0]['seqNo'] is not None

    req99, _ = await payment.build_get_payment_sources_request(wallet_handler, None, address)
    res99 = json.loads(await ledger.submit_request(pool_handler, req99))
    assert res99['op'] == 'REPLY' and res99['result']['outputs'] == []

    req10, _ = await payment.build_verify_payment_req(wallet_handler, None, receipt['receipt'])
    res10 = json.loads(await ledger.submit_request(pool_handler, req10))
    assert res10['result']['seqNo'] is not None

    # no seqno returned for this txn type
    req11 = await ledger.build_get_auth_rule_request(None, '101', 'ADD', '*', None, '*')
    res11 = json.loads(await ledger.submit_request(pool_handler, req11))
    assert res11['op'] == 'REPLY'
    assert res11['result']['data'] is not None

    req12 = await payment.build_get_txn_fees_req(wallet_handler, None, libsovtoken_payment_method)
    res12 = json.loads(await ledger.submit_request(pool_handler, req12))
    assert res12['op'] == 'REPLY'
    assert res12['result']['fees'] is not None

    req13 = await ledger.build_get_acceptance_mechanisms_request(None, None, 'AML version')
    res13 = json.loads(await ledger.submit_request(pool_handler, req13))
    assert res13['op'] == 'REPLY'
    assert res13['result']['seqNo'] is not None

    req14 = await ledger.build_get_txn_author_agreement_request(None, json.dumps({'version': 'TAA version'}))
    res14 = json.loads(await ledger.submit_request(pool_handler, req14))
    assert res14['op'] == 'REPLY'
    assert res14['result']['seqNo'] is not None
