import pytest
import time
import logging
import asyncio
from indy import *
from indy.error import IndyError
from system.utils import *
import testinfra
import os
import subprocess
import numpy as np
from random import randrange as rr
from random import sample
from datetime import datetime, timedelta, timezone
import hashlib
from hypothesis import errors, settings, Verbosity, given, strategies
import pprint
import itertools
import docker


# logger = logging.getLogger(__name__)
# logging.basicConfig(
#     level=0, format='%(asctime)s %(message)s', filename='client_log', filemode='a'
# )


@pytest.mark.asyncio
async def test_misc_get_nonexistent():
    await pool.set_protocol_version(2)
    timestamp0 = int(time.time())
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    submitter_did, submitter_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    timestamp1 = int(time.time())

    res1 = json.dumps(
        await get_schema(pool_handle, wallet_handle, submitter_did, 'WKWN6U6XKTFxJBC3mB7Pdo:2:schema1:1.0'))
    res2 = json.dumps(
        await get_cred_def(pool_handle, wallet_handle, submitter_did, '3VTSJXBKw2DBjfaJt4eS1X:3:CL:685:TAG'))
    res3 = json.dumps(
        await get_revoc_reg_def(
            pool_handle, wallet_handle, submitter_did,
            'RgTvEeKFSxd2Fcsxh42k9T:4:RgTvEeKFSxd2Fcsxh42k9T:3:CL:689:cred_def_tag:CL_ACCUM:revoc_def_tag'))
    res4 = json.dumps(
        await get_revoc_reg(
            pool_handle, wallet_handle, submitter_did,
            'RgTvEeKFSxd2Fcsxh42k9T:4:RgTvEeKFSxd2Fcsxh42k9T:3:CL:689:cred_def_tag:CL_ACCUM:revoc_def_tag',
            timestamp0))
    res5 = json.dumps(
        await get_revoc_reg_delta(
            pool_handle, wallet_handle, submitter_did,
            'RgTvEeKFSxd2Fcsxh42k9T:4:RgTvEeKFSxd2Fcsxh42k9T:3:CL:689:cred_def_tag:CL_ACCUM:revoc_def_tag',
            timestamp0, timestamp1))

    with pytest.raises(IndyError, match='LedgerNotFound'):
        await ledger.parse_get_schema_response(res1)

    with pytest.raises(IndyError, match='LedgerNotFound'):
        await ledger.parse_get_cred_def_response(res2)

    with pytest.raises(IndyError, match='LedgerNotFound'):
        await ledger.parse_get_revoc_reg_def_response(res3)

    with pytest.raises(IndyError, match='LedgerNotFound'):
        await ledger.parse_get_revoc_reg_response(res4)

    with pytest.raises(IndyError, match='LedgerNotFound'):
        await ledger.parse_get_revoc_reg_delta_response(res5)


# @pytest.mark.skip
@pytest.mark.asyncio
async def test_misc_wallet():
    wallet_handle, _, _ = await wallet_helper('abc', 'abc', 'ARGON2I_MOD')
    await did.create_and_store_my_did(wallet_handle, json.dumps({'seed': '000000000000000000000000Trustee1'}))


@pytest.mark.asyncio
async def test_misc_get_txn_by_seqno():
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    req = await ledger.build_get_txn_request(None, None, 1)
    res = await ledger.submit_request(pool_handle, req)
    print(res)


@pytest.mark.asyncio
async def test_misc_state_proof(
        docker_setup_and_teardown, payment_init, pool_handler, wallet_handler, get_default_trustee,
        initial_token_minting
):
    trustee_did, _ = get_default_trustee
    random_did = random_did_and_json()[0]
    address = initial_token_minting
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
    await asyncio.sleep(1)
    timestamp0 = int(time.time())
    res = json.dumps(await get_schema(pool_handler, wallet_handler, trustee_did, schema_id))
    schema_id, schema_json = await ledger.parse_get_schema_response(res)
    cred_def_id, _, res_cred_def = await send_cred_def(
        pool_handler, wallet_handler, trustee_did, schema_json, random_string(3), None, json.dumps(
            {'support_revocation': True}
        )
    )
    assert res_cred_def['op'] == 'REPLY'
    revoc_reg_def_id, _, _, res_entry = await send_revoc_reg_entry(
        pool_handler, wallet_handler, trustee_did, 'CL_ACCUM', random_string(3), cred_def_id, json.dumps(
            {'max_cred_num': 1, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}
        )
    )
    assert res_entry['op'] == 'REPLY'
    timestamp1 = int(time.time())

    # uncomment to check freshness state proof reading
    # await asyncio.sleep(600)

    hosts = [testinfra.get_host('docker://node' + str(i)) for i in range(1, 8)]
    print(hosts)
    outputs0 = [host.run('systemctl stop indy-node') for host in hosts[:-1]]
    print(outputs0)
    try:
        req1 = await ledger.build_get_nym_request(None, random_did)
        res1 = json.loads(await ledger.submit_request(pool_handler, req1))

        req2 = await ledger.build_get_attrib_request(None, random_did, 'key', None, None)
        res2 = json.loads(await ledger.submit_request(pool_handler, req2))

        req3 = await ledger.build_get_schema_request(None, schema_id)
        res3 = json.loads(await ledger.submit_request(pool_handler, req3))

        req4 = await ledger.build_get_cred_def_request(None, cred_def_id)
        res4 = json.loads(await ledger.submit_request(pool_handler, req4))

        req5 = await ledger.build_get_revoc_reg_def_request(None, revoc_reg_def_id)
        res5 = json.loads(await ledger.submit_request(pool_handler, req5))

        # consensus is impossible with timestamp0 here! IS-1263
        req6 = await ledger.build_get_revoc_reg_request(None, revoc_reg_def_id, timestamp1)
        res6 = json.loads(await ledger.submit_request(pool_handler, req6))

        req66 = await ledger.build_get_revoc_reg_request(None, revoc_reg_def_id, timestamp0)
        res66 = json.loads(await ledger.submit_request(pool_handler, req66))

        # consensus is impossible with (timestamp0, timestamp1) here! IS-1264
        req7 = await ledger.build_get_revoc_reg_delta_request(None, revoc_reg_def_id, timestamp0, timestamp1)
        res7 = json.loads(await ledger.submit_request(pool_handler, req7))

        # tokens
        req8, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address)
        res8 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req8))
    finally:
        outputs1 = [host.run('systemctl start indy-node') for host in hosts[:-1]]
        print(outputs1)

    assert res1['result']['seqNo'] is not None
    assert res2['result']['seqNo'] is not None
    assert res3['result']['seqNo'] is not None
    assert res4['result']['seqNo'] is not None
    assert res5['result']['seqNo'] is not None
    assert res6['result']['seqNo'] is not None
    print(res66)
    assert res66['result']['seqNo'] is None
    assert res7['result']['seqNo'] is not None
    assert res8['op'] == 'REPLY' and res8['result']['outputs'][0]['seqNo'] is not None


@pytest.mark.asyncio
async def test_misc_stn_slowness():
    await pool.set_protocol_version(2)
    schema_timings = []
    cred_def_timings = []
    nodes = ['NodeTwinPeek', 'RFCU', 'australia', 'brazil', 'canada', 'england', 'ibmTest', 'korea', 'lab10',
             'singapore', 'virginia', 'vnode1', 'xsvalidatorec2irl']
    for i in range(10):
        for node in nodes:
            pool_handle, _ = await pool_helper(path_to_genesis='./stn_genesis', node_list=[node, ])

            t1 = time.perf_counter()
            req1 = await ledger.build_get_schema_request(None,
                                                         'Rvk7x5oSFwoLWZK8rM1Anf:2:Passport Office1539941790480:1.0')
            schema_build_time = time.perf_counter() - t1
            await ledger.submit_request(pool_handle, req1)
            schema_submit_time = time.perf_counter() - t1 - schema_build_time
            schema_timings.append(schema_submit_time)
            print('ITERATION: ', i, '\t', 'NODE: ', node, '\t',
                  'SCHEMA BUILD TIME: ', schema_build_time, '\t', 'SCHEMA SUBMIT TIME: ', schema_submit_time)

            t2 = time.perf_counter()
            req2 = await ledger.build_get_cred_def_request(None, 'Rvk7x5oSFwoLWZK8rM1Anf:3:CL:9726:tag1')
            cred_def_build_time = time.perf_counter() - t2
            await ledger.submit_request(pool_handle, req2)
            cred_def_submit_time = time.perf_counter() - t2 - cred_def_build_time
            cred_def_timings.append(cred_def_submit_time)
            print('ITERATION: ', i, '\t', 'NODE: ', node, '\t',
                  'CRED DEF BUILD TIME: ', cred_def_build_time, '\t', 'CRED DEF SUBMIT TIME: ', cred_def_submit_time)

    print('SCHEMA_SUBMIT_AVG', np.average(schema_timings))
    print('CRED_DEF_SUBMIT_AVG', np.average(cred_def_timings))

    assert np.mean(schema_timings) < 1.5
    assert np.mean(cred_def_timings) < 0.5


@pytest.mark.asyncio
async def test_new_role():
    # INDY-1916 / IS-1123
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    role_under_test = 'NETWORK_MONITOR'

    did1, vk1 = await did.create_and_store_my_did(wallet_handle, '{}')
    did2, vk2 = await did.create_and_store_my_did(wallet_handle, '{}')
    did3, vk3 = await did.create_and_store_my_did(wallet_handle, '{}')
    did4, vk4 = await did.create_and_store_my_did(wallet_handle, '{}')
    did5, vk5 = await did.create_and_store_my_did(wallet_handle, '{}')

    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    steward_did, steward_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Steward1'}))
    anchor_did, anchor_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    await send_nym(pool_handle, wallet_handle, trustee_did, anchor_did, anchor_vk, 'trust anchor', 'TRUST_ANCHOR')
    user_did, user_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    await send_nym(pool_handle, wallet_handle, trustee_did, user_did, user_vk, 'user without role', None)

    # Trustee adds NETWORK_MONITOR NYM
    res1 = await send_nym(pool_handle, wallet_handle, trustee_did, did1, vk1, None, role_under_test)
    assert res1['op'] == 'REPLY'
    # Steward adds NETWORK_MONITOR NYM
    res2 = await send_nym(pool_handle, wallet_handle, steward_did, did2, vk2, None, role_under_test)
    assert res2['op'] == 'REPLY'
    # Trust Anchor adds NETWORK_MONITOR NYM - should fail
    res3 = await send_nym(pool_handle, wallet_handle, anchor_did, did3, vk3, None, role_under_test)
    assert res3['op'] == 'REJECT'
    # User adds NETWORK_MONITOR NYM - should fail
    res4 = await send_nym(pool_handle, wallet_handle, user_did, did4, vk4, None, role_under_test)
    assert res4['op'] == 'REJECT'
    # NETWORK_MONITOR adds NETWORK_MONITOR NYM - should fail
    res5 = await send_nym(pool_handle, wallet_handle, did1, did5, vk5, None, role_under_test)
    assert res5['op'] == 'REJECT'

    req = await ledger.build_get_validator_info_request(trustee_did)
    res_t = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))

    req = await ledger.build_get_validator_info_request(steward_did)
    res_s = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, steward_did, req))

    req = await ledger.build_get_validator_info_request(did1)
    res_nm = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, did1, req))

    assert res_t.keys() == res_s.keys() == res_nm.keys()

    # NETWORK_MONITOR adds user NYM - should fail
    add_nym = await send_nym(pool_handle, wallet_handle, did1, did5, vk5, None, None)
    assert add_nym['op'] == 'REJECT'
    # NETWORK_MONITOR sends pool restart - should fail
    req = await ledger.build_pool_restart_request(did1, 'start', '0')
    pool_restart = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, did1, req))
    pool_restart = json.loads(sample(pool_restart.items(), 1)[0][1])
    assert pool_restart['op'] == 'REJECT'
    # NETWORK_MONITOR sends pool config - should fail
    req = await ledger.build_pool_config_request(did1, False, True)
    pool_config = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, did1, req))
    assert pool_config['op'] == 'REQNACK'

    # Trust Anchor removes NETWORK_MONITOR role - should fail
    res6 = await send_nym(pool_handle, wallet_handle, anchor_did, did1, None, None, '')
    assert res6['op'] == 'REJECT'
    # Trustee removes NETWORK_MONITOR role (that was added by Steward)
    res7 = await send_nym(pool_handle, wallet_handle, trustee_did, did2, None, None, '')
    assert res7['op'] == 'REPLY'
    # Steward removes NETWORK_MONITOR role (that was added by Trustee)
    res8 = await send_nym(pool_handle, wallet_handle, steward_did, did1, None, None, '')
    assert res8['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_pool_config():
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    new_steward_did, new_steward_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    await send_nym(pool_handle, wallet_handle, trustee_did, new_steward_did, new_steward_vk, 'steward', 'STEWARD')

    res0 = await send_nym(pool_handle, wallet_handle, trustee_did, random_did_and_json()[0])
    assert res0['op'] == 'REPLY'

    data = json.dumps(
            {
                  'alias': random_string(5),
                  'client_ip': '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                  'client_port': rr(1, 32767),
                  'node_ip': '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                  'node_port': rr(1, 32767),
                  'services': ['VALIDATOR']
            })
    req = await ledger.build_node_request(new_steward_did, 'koKn32jREPYR642DQsFftPoCkTf3XCPcfvc3x9RhRK7', data)
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, new_steward_did, req))
    assert res1['op'] == 'REPLY'

    req = await ledger.build_pool_config_request(trustee_did, True, False)
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    assert res2['op'] == 'REPLY'

    res3 = await send_nym(pool_handle, wallet_handle, trustee_did, random_did_and_json()[0])
    assert res3['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_error_handling(pool_handler, wallet_handler):
    d, vk = await did.create_and_store_my_did(wallet_handler, '{}')
    print()
    with pytest.raises(IndyError) as e1:
        await anoncreds.issuer_create_schema(d, random_string(5), random_string(5), json.dumps([{}]))
    print(e1)
    with pytest.raises(IndyError) as e2:
        await crypto.get_key_metadata(wallet_handler, random_string(10))
    print(e2)
    with pytest.raises(IndyError) as e3:
        await did.create_and_store_my_did(wallet_handler, json.dumps({'did': ''}))
    print(e3)
    with pytest.raises(IndyError) as e4:
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, '3fyKjNLV6foqDxoEbBiQhY', json.dumps({}))
    print(e4)
    with pytest.raises(IndyError) as e5:
        await non_secrets.add_wallet_record(0, random_string(1), random_string(2), random_string(3),
                                            json.dumps({}))
    print(e5)
    with pytest.raises(IndyError) as e6:
        await pairwise.create_pairwise(wallet_handler, '', '', None)
    print(e6)
    with pytest.raises(IndyError) as e7:
        await pool.create_pool_ledger_config('docker', None)  # already exists
    print(e7)
    with pytest.raises(IndyError) as e8:
        await wallet.create_wallet(json.dumps({}), json.dumps({}))
    print(e8)


@pytest.mark.asyncio
async def test_misc_vi_freshness(pool_handler, wallet_handler, get_default_trustee):
    # INDY-1928
    trustee_did, _ = get_default_trustee
    req = await ledger.build_get_validator_info_request(trustee_did)
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    res = json.loads(sample(res.items(), 1)[0][1])
    assert res['result']['data']['Node_info']['Freshness_status']['0']['Has_write_consensus'] is True
    assert res['result']['data']['Node_info']['Freshness_status']['0']['Last_updated_time']


@pytest.mark.parametrize('role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', 'NETWORK_MONITOR'])
@pytest.mark.asyncio
async def test_misc_permission_error_messages(pool_handler, wallet_handler, get_default_trustee, role):
    # INDY-1963
    trustee_did, _ = get_default_trustee
    did1, vk1 = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, vk2 = await did.create_and_store_my_did(wallet_handler, '{}')
    await send_nym(pool_handler, wallet_handler, trustee_did, did1, vk1, None, role)

    res1 = await send_nym(pool_handler, wallet_handler, trustee_did, did1, vk2, None, None)
    assert (res1['op'] == 'REJECT') &\
           (res1['reason'].find('can not touch verkey field since only the owner can modify it') is not -1)

    await send_nym(pool_handler, wallet_handler, trustee_did, did1, None, None, '')

    res2 = await send_nym(pool_handler, wallet_handler, did1, did2, vk2, None, None)
    assert (res2['op'] == 'REJECT') & (res2['reason'].find('Rule for this action is') is not -1)


@pytest.mark.asyncio
async def test_misc_indy_1933(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    # INDY-1933
    trustee_did, _ = get_default_trustee
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
    nodes = ['node2', 'node3']
    outputs = [subprocess.check_call(['docker', 'exec', '-d', node, 'stress', '-c', '1', '-i', '1', '-m', '1'])
               for node in nodes]
    # hosts = [testinfra.get_host('docker://node' + str(i)) for i in range(2, 4)]
    # outputs = [host.run('stress -c 1 -i 1 -m 1 & disown') for host in hosts]
    print(outputs)
    for i in range(200):
        await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    dict_results = {key: json.loads(results[key]) for key in results}
    print(dict_results)
    assert all([dict_results[key]['op'] == 'REPLY' for key in dict_results])


@pytest.mark.asyncio
async def test_misc_is_1158(pool_handler, wallet_handler, get_default_trustee):
    issuer_did, _ = get_default_trustee
    prover_did, prover_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    schema_id, s_res = await send_schema(pool_handler, wallet_handler, issuer_did, random_string(5), '1.0',
                                         json.dumps(["hash", "enc", "raw"]))
    assert s_res['op'] == 'REPLY'
    res = await get_schema(pool_handler, wallet_handler, issuer_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, cred_def_json, c_res = await send_cred_def(pool_handler, wallet_handler, issuer_did, schema_json,
                                                            random_string(3), None,
                                                            json.dumps({'support_revocation': False}))
    assert c_res['op'] == 'REPLY'
    master_secret_id = await anoncreds.prover_create_master_secret(wallet_handler, None)
    cred_offer = await anoncreds.issuer_create_credential_offer(wallet_handler, cred_def_id)
    assert cred_offer is not None
    cred_req, cred_req_metadata = await anoncreds.prover_create_credential_req(wallet_handler, prover_did, cred_offer,
                                                                               cred_def_json, master_secret_id)
    cred_values = json.dumps({
        "hash": {"raw": random_string(10), "encoded": "5944657099558967239210949205008160769251991705004233"},
        "enc": {"raw": "100", "encoded": "594967239210949258394887428692050081607692519917050033"},
        "raw": {"raw": random_string(10), "encoded": "59446570995589672392109492583948874286920500816"}
    })
    cred_json, _, _ = await anoncreds.issuer_create_credential(wallet_handler, cred_offer, cred_req, cred_values,
                                                               None, None)
    assert cred_json is not None


@pytest.mark.asyncio
async def test_misc_audit_ledger(pool_handler, wallet_handler, get_default_trustee):
    node_to_stop = '7'
    host = testinfra.get_host('ssh://node'+node_to_stop)
    trustee_did, _ = get_default_trustee
    # # it doesn't work
    # os.system('perf_processes.py -g docker_genesis -n 1 -y one '
    #           '-k '
    #           '\"[{\"nym\":{\"count\": 1}}, '
    #           '{\"demoted_node\":{\"count\": 1}}, '
    #           '{\"cfg_writes\":{\"count\": 1}}]\" '
    #           '-c 1 -b 1 -l 1 >> /dev/null &')
    for i in range(25):
        steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, 'STEWARD')
        req1 = await ledger.build_node_request(steward_did, steward_vk,
                                               json.dumps(
                                                        {
                                                            'alias': random_string(5),
                                                            'client_ip':
                                                                '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                                                            'client_port': rr(1, 32767),
                                                            'node_ip':
                                                                '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                                                            'node_port': rr(1, 32767),
                                                            'services': []
                                                        }))
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req1)
        # req2 = json.loads(req1)
        # req2['operation']['data']['services'] = []
        # await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, json.dumps(req2))
        req3 = await ledger.build_pool_config_request(trustee_did, True, False)
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req3)
    output = host.check_output('systemctl stop indy-node')
    print(output)
    for i in range(25):
        steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, 'STEWARD')
        req1 = await ledger.build_node_request(steward_did, steward_vk,
                                               json.dumps(
                                                        {
                                                            'alias': random_string(5),
                                                            'client_ip':
                                                                '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                                                            'client_port': rr(1, 32767),
                                                            'node_ip':
                                                                '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                                                            'node_port': rr(1, 32767),
                                                            'services': []
                                                        }))
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req1)
        # req2 = json.loads(req1)
        # req2['operation']['data']['services'] = []
        # await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, json.dumps(req2))
        req3 = await ledger.build_pool_config_request(trustee_did, True, False)
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req3)
    # os.system('pkill -9 perf_processes')
    output = host.check_output('systemctl start indy-node')
    print(output)
    await asyncio.sleep(60)
    await check_pool_is_in_sync()


# @pytest.mark.parametrize('txn_type, action, field, old, new, constraint', [
#     (),
#     (),
#     ()
# ])
@pytest.mark.asyncio
async def test_misc_is_1201(pool_handler, wallet_handler, get_default_trustee,
                            txn_type, action, field, old, new, constraint):
    trustee_did, _ = get_default_trustee
    req = await ledger.build_auth_rule_request(trustee_did, txn_type, action, field, old, new, constraint)
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res)
    assert res['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_nodes_adding(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, 'STEWARD')
    req1 = await ledger.build_node_request(steward_did, steward_vk,
                                           json.dumps(
                                                  {
                                                      'alias': random_string(5),
                                                      'client_ip':
                                                          '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                                                      'client_port': rr(1, 32767),
                                                      'node_ip':
                                                          '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                                                      'node_port': rr(1, 32767),
                                                      'services': ['VALIDATOR']
                                                  }))
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req1))
    print(res1)
    assert res1['op'] == 'REPLY'
    req2 = await ledger.build_node_request(steward_did, steward_vk,
                                           json.dumps(
                                                  {
                                                      'alias': random_string(5),
                                                      'client_ip':
                                                          '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                                                      'client_port': rr(1, 32767),
                                                      'node_ip':
                                                          '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                                                      'node_port': rr(1, 32767),
                                                      'services': ['VALIDATOR']
                                                  }))
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req2))
    print(res2)
    assert res2['op'] == 'REJECT'


@pytest.mark.asyncio
async def test_misc_indy_1554_can_write_true(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    await send_nym(pool_handler, wallet_handler, trustee_did, new_did, new_vk, None, None)

    schema_id, _ = await send_schema(pool_handler, wallet_handler, new_did,
                                       'schema1', '1.0', json.dumps(["age", "sex", "height", "name"]))
    await asyncio.sleep(1)
    res = await get_schema(pool_handler, wallet_handler, new_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, _, res = await send_cred_def(pool_handler, wallet_handler, new_did, schema_json, 'cred_def_tag',
                                                'CL', json.dumps({'support_revocation': True}))
    revoc_reg_def_id, _, _, res1 = await send_revoc_reg_entry(pool_handler, wallet_handler, new_did, 'CL_ACCUM',
                                                                'revoc_def_tag', cred_def_id,
                                                              json.dumps({'max_cred_num': 1,
                                                                            'issuance_type': 'ISSUANCE_BY_DEFAULT'}))
    print(res1)
    revoc_reg_def_id, _, _, res9 = await send_revoc_reg_entry(pool_handler, wallet_handler, trustee_did, 'CL_ACCUM',
                                                                'another_revoc_def_tag', cred_def_id,
                                                              json.dumps({'max_cred_num': 1,
                                                                            'issuance_type': 'ISSUANCE_BY_DEFAULT'}))
    print(res9)

    assert res1['op'] == 'REPLY'
    assert res9['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_indy_1554_can_write_false(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    t_did, t_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    await send_nym(pool_handler, wallet_handler, trustee_did, new_did, new_vk, None, None)
    await send_nym(pool_handler, wallet_handler, trustee_did, t_did, t_vk, None, 'TRUSTEE')

    schema_id, _ = await send_schema(pool_handler, wallet_handler, trustee_did,
                                       'schema1', '1.0', json.dumps(["age", "sex", "height", "name"]))
    await asyncio.sleep(1)
    res = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, _, res = await send_cred_def(pool_handler, wallet_handler, trustee_did, schema_json, 'cred_def_tag',
                                                'CL', json.dumps({'support_revocation': True}))
    # Creation by None role- FAIL
    revoc_reg_def_id1, revoc_reg_def_json1, revoc_reg_entry_json1, res1 = \
        await send_revoc_reg_entry(pool_handler, wallet_handler, new_did, 'CL_ACCUM', 'revoc_def_tag', cred_def_id,
                                   json.dumps({'max_cred_num': 1, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}))

    print(res1)
    # Creation by Trustee role - PASS
    revoc_reg_def_id2, revoc_reg_def_json2, revoc_reg_entry_json2, res2 = \
        await send_revoc_reg_entry(pool_handler, wallet_handler, trustee_did, 'CL_ACCUM', 'another_revoc_def_tag',
                                   cred_def_id, json.dumps({'max_cred_num': 1, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}))
    print(res2)

    # Editing by None role and not owner both entities
    req = await ledger.build_revoc_reg_def_request(new_did, revoc_reg_def_json2)
    res3 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, new_did, req)
    print(res3)
    req = await ledger.build_revoc_reg_entry_request(new_did, revoc_reg_def_id2, 'CL_ACCUM', revoc_reg_entry_json2)
    res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, new_did, req))
    print(res4)

    # Editing by Trustee role and not owner both entities
    req = await ledger.build_revoc_reg_def_request(t_did, revoc_reg_def_json2)
    res5 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, t_did, req)
    print(res5)
    req = await ledger.build_revoc_reg_entry_request(t_did, revoc_reg_def_id2, 'CL_ACCUM', revoc_reg_entry_json2)
    res6 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, t_did, req))
    print(res6)

    # Editing by Trustee role and owner both entities
    req = await ledger.build_revoc_reg_def_request(trustee_did, revoc_reg_def_json2)
    res7 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    print(res7)
    req = await ledger.build_revoc_reg_entry_request(trustee_did, revoc_reg_def_id2, 'CL_ACCUM', revoc_reg_entry_json2)
    res8 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res8)

    assert res1['op'] == 'REJECT'  # UnauthorizedClientRequest Rule for this action is...
    assert res2['op'] == 'REPLY'


@pytest.mark.parametrize('submitter_did, txn_type, action, field, old_value, new_value', [
    (None, None, None, None, None, None),
    (None, 'NYM', 'ADD', 'role', None, '101'),
    (None, 'NYM', 'EDIT', 'role', '0', '101'),
    (None, 'NYM', 'ADD', 'role', None, '2'),
    (None, 'NYM', 'EDIT', 'role', '0', '2'),
    (None, 'ATTRIB', 'ADD', '*', '*', '*'),
    (None, 'ATTRIB', 'EDIT', '*', '*', '*'),
    (None, 'SCHEMA', 'ADD', '*', '*', '*'),
    (None, 'SCHEMA', 'EDIT', '*', '*', '*'),
    (None, 'CRED_DEF', 'ADD', '*', '*', '*'),
    (None, 'CRED_DEF', 'EDIT', '*', '*', '*'),
    (None, 'REVOC_REG_DEF', 'ADD', '*', '*', '*'),
    (None, 'REVOC_REG_DEF', 'EDIT', '*', '*', '*'),
    (None, 'REVOC_REG_ENTRY', 'ADD', '*', '*', '*'),
    (None, 'REVOC_REG_ENTRY', 'EDIT', '*', '*', '*'),
])
@pytest.mark.asyncio
async def test_misc_is_1202(pool_handler, wallet_handler, get_default_trustee,
                            submitter_did, txn_type, action, field, old_value, new_value):
    trustee_did, _ = get_default_trustee
    req = await ledger.build_get_auth_rule_request(submitter_did, txn_type, action, field, old_value, new_value)
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print('\n', res)
    assert res['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_is_1085(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    res = await get_nym(pool_handler, wallet_handler, trustee_did, trustee_did)
    print(res)


@pytest.mark.asyncio
async def test_misc_indy_2022(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    results1 = []
    for i in range(5):
        res = await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        results1.append(res)
    assert all([res['op'] == 'REPLY' for res in results1])
    await asyncio.sleep(720)
    primary, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
    output = testinfra.get_host('ssh://node{}'.format(primary)).check_output('systemctl restart indy-node')
    print(output)
    results2 = []
    for i in range(10):
        res = await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        results2.append(res)
    assert all([res['op'] == 'REPLY' for res in results2])
    await asyncio.sleep(15)
    await check_pool_is_in_sync()


@settings(verbosity=Verbosity.debug, deadline=2000.0, max_examples=100)
@given(h_text=strategies.text(alphabet=strategies.characters(whitelist_categories=('L', 'Sc')),
                              min_size=5,
                              max_size=50),
       h_first_number=strategies.integers(min_value=0, max_value=999),
       h_last_number=strategies.integers(min_value=999, max_value=99999))
def test_misc_hypothesis_sync(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
                              h_text, h_first_number, h_last_number):
    trustee_did, _ = get_default_trustee
    res = run_async_method(send_schema, pool_handler, wallet_handler, trustee_did, h_text,
                           str(h_first_number)+'.'+str(h_last_number),
                           json.dumps([random_string(10), random_string(25)]))
    print(res[1])
    assert res[1]['op'] == 'REPLY'


@settings(verbosity=Verbosity.debug, deadline=2000.0, max_examples=100)
@given(h_text=strategies.text(alphabet=strategies.characters(whitelist_categories=('L', 'Sc')),
                              min_size=5,
                              max_size=50),
       h_first_number=strategies.integers(min_value=0, max_value=999),
       h_last_number=strategies.integers(min_value=999, max_value=99999))
@pytest.mark.asyncio
async def test_misc_hypothesis_async(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
                                     h_text, h_first_number, h_last_number):
    trustee_did, _ = get_default_trustee
    res = await send_schema(pool_handler, wallet_handler, trustee_did, h_text,
                            str(h_first_number)+'.'+str(h_last_number),
                            json.dumps([random_string(10), random_string(25)]))
    print(res[1])
    assert res[1]['op'] == 'REPLY'


@pytest.mark.parametrize('role_under_test', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', 'NETWORK_MONITOR'])
@pytest.mark.asyncio
async def test_misc_indy_2033(pool_handler, wallet_handler, get_default_trustee, role_under_test):
    trustee_did, _ = get_default_trustee
    # another_trustee_did, another_trustee_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    new_did, new_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    # res0 = await nym_helper(pool_handler, wallet_handler, trustee_did, another_trustee_did, another_trustee_vk, None,
    #                         'TRUSTEE')
    # print('\n{}'.format(res0))
    # assert res0['op'] == 'REPLY'
    res1 = await send_nym(pool_handler, wallet_handler, trustee_did, new_did, new_vk, None, role_under_test)
    print('\n{}'.format(res1))
    assert res1['op'] == 'REPLY'
    res2 = await send_nym(pool_handler, wallet_handler, trustee_did, new_did, None, None, '')
    print('\n{}'.format(res2))
    assert res2['op'] == 'REPLY'
    res3 = await send_nym(pool_handler, wallet_handler, trustee_did, new_did, None, None, role_under_test)
    print('\n{}'.format(res3))
    assert res3['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_indy_1720(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    primary1, alias1, target_did1 = await get_primary(pool_handler, wallet_handler, trustee_did)
    await demote_node(pool_handler, wallet_handler, trustee_did, alias1, target_did1)
    primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
    assert primary2 != primary1
    for i in range(100):
        await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
    await promote_node(pool_handler, wallet_handler, trustee_did, alias1, target_did1)
    primary3 = await wait_until_vc_is_done(primary2, pool_handler, wallet_handler, trustee_did)
    assert primary3 != primary2
    output = testinfra.get_host('ssh://node{}'.format(primary3)).check_output('systemctl stop indy-node')
    print(output)
    primary4 = await wait_until_vc_is_done(primary3, pool_handler, wallet_handler, trustee_did)
    assert primary4 != primary3
    for i in range(100):
        await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
    output = testinfra.get_host('ssh://node{}'.format(primary3)).check_output('systemctl start indy-node')
    print(output)
    await check_pool_is_in_sync()
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])


@pytest.mark.repeat(3)
@pytest.mark.asyncio
async def test_misc_is_1237(get_default_trustee):
    print()
    trustee_did, _ = get_default_trustee
    req1 = json.loads(await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '',
                                                           json.dumps({
                                                                'constraint_id': 'ROLE',
                                                                'role': '*',
                                                                'sig_count': 1,
                                                                'need_to_be_owner': False,
                                                                'metadata': {}
                                                           })))
    pprint.pprint(req1)
    req2 = json.loads(await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '*', None,
                                                           json.dumps({
                                                                'constraint_id': 'ROLE',
                                                                'role': '*',
                                                                'sig_count': 1,
                                                                'need_to_be_owner': False,
                                                                'metadata': {}
                                                           })))
    pprint.pprint(req2)


@pytest.mark.asyncio
async def test_case_nym_special_case(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    reader_did, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res1 = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk)
    assert res1['op'] == 'REPLY'
    res2 = await send_nym(pool_handler, wallet_handler, trustee_did, new_did)
    print(res2)
    res3 = await send_nym(pool_handler, wallet_handler, editor_did, new_did)
    print(res3)
    res4 = await get_nym(pool_handler, wallet_handler, reader_did, new_did)
    print(res4)


@settings(deadline=None, max_examples=100)
@given(target_alias=strategies.text(alphabet=strategies.characters(whitelist_categories=('L', 'N', 'S')),
                                    min_size=1,
                                    max_size=100))
@pytest.mark.asyncio
async def test_misc_nym_alias(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
                              target_alias):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(pool_handler, wallet_handler, trustee_did,
                         new_did, None, target_alias, None)
    print(res)
    assert res['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_mint_to_aws(payment_init):
    await pool.set_protocol_version(2)
    libsovtoken_payment_method = 'sov'
    pool_handle, _ = await pool_helper(path_to_genesis='../aws_genesis_test')
    # pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': str('000000000000000000000000Trustee1')}))
    trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {"seed": str('000000000000000000000000Trustee2')}))
    trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {"seed": str('000000000000000000000000Trustee3')}))
    await send_nym(pool_handle, wallet_handle, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
    await send_nym(pool_handle, wallet_handle, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')

    addresses = []
    for i in range(10):
        address = await payment.create_payment_address(wallet_handle, libsovtoken_payment_method, json.dumps({}))
        addresses.append(address)

    outputs = []
    for address in addresses:
        output = {"recipient": address, "amount": 8000000000*100000}
        outputs.append(output)

    req, _ = await payment.build_mint_req(wallet_handle, trustee_did,
                                          json.dumps(outputs), None)
    req = await ledger.multi_sign_request(wallet_handle, trustee_did, req)
    req = await ledger.multi_sign_request(wallet_handle, trustee_did2, req)
    req = await ledger.multi_sign_request(wallet_handle, trustee_did3, req)
    res1 = json.loads(await ledger.submit_request(pool_handle, req))
    print(res1)
    assert res1['op'] == 'REPLY'


@settings(deadline=None, max_examples=250)
@given(amount=strategies.text(min_size=1, max_size=10000))
@pytest.mark.asyncio
async def test_misc_mint_manually(
        docker_setup_and_teardown, payment_init, pool_handler, wallet_handler, get_default_trustee, amount
):
    libsovtoken_payment_method = 'sov'
    trustee_did, _ = get_default_trustee
    try:
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
    except IndyError:
        trustee_did2, trustee_vk2 = 'LnXR1rPnncTPZvRdmJKhJQ', 'BnSWTUQmdYCewSGFrRUhT6LmKdcCcSzRGqWXMPnEP168'
        trustee_did3, trustee_vk3 = 'PNQm3CwyXbN5e39Rw3dXYx', 'DC8gEkb1cb4T9n3FcZghTkSp1cGJaZjhsPdxitcu6LUj'
    address = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps({}))
    req = json.dumps(
        {"operation":
             {"type": "10000",
              "outputs":
                  [{"address": address.split(':')[-1],
                    "amount": amount}]},
         "reqId": int(time.time()),
         "protocolVersion": 2,
         "identifier": "V4SGRU86Z58d6TV7PBUe6f"})
    req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
    res = json.loads(await ledger.submit_request(pool_handler, req))
    print('\n{}:{}'.format(amount, res))
    assert res['op'] == 'REQNACK'
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)


@pytest.mark.asyncio
async def test_misc_plug_req_handlers_regression(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee

    req1 = await ledger.build_get_validator_info_request(trustee_did)
    t0 = time.perf_counter()
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req1))
    t1 = time.perf_counter()
    print(res1)
    print('\n{}\n'.format(t1 - t0))
    assert (t1 - t0) < 1.0
    res1 = {k: json.loads(v) for k, v in res1.items()}
    assert all([v['op'] == 'REPLY' for k, v in res1.items()])

    req2 = await ledger.build_pool_restart_request(trustee_did, 'start', '0')
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req2))
    print(res2)
    res2 = {k: json.loads(v) for k, v in res2.items()}
    assert all([v['op'] == 'REPLY' for k, v in res2.items()])


@pytest.mark.asyncio
async def test_misc_utxo_st_600_604(
        docker_setup_and_teardown, payment_init, pool_handler, wallet_handler, get_default_trustee
):
    hosts = [testinfra.get_host('docker://node' + str(i)) for i in range(1, 8)]
    print(hosts)
    libsovtoken_payment_method = 'sov'
    trustee_did, _ = get_default_trustee
    address0 = await payment.create_payment_address(
        wallet_handler, libsovtoken_payment_method, json.dumps({"seed": str('0000000000000000000000000Wallet0')})
    )
    try:
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
    except IndyError:
        trustee_did2, trustee_vk2 = 'LnXR1rPnncTPZvRdmJKhJQ', 'BnSWTUQmdYCewSGFrRUhT6LmKdcCcSzRGqWXMPnEP168'
        trustee_did3, trustee_vk3 = 'PNQm3CwyXbN5e39Rw3dXYx', 'DC8gEkb1cb4T9n3FcZghTkSp1cGJaZjhsPdxitcu6LUj'

    addresses = []
    outputs = []

    for i in range(1):
        addresses.append([])
        outputs.append([])
        for j in range(1500):
            address = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps({}))
            addresses[i].append(address)
            output = {"recipient": address, "amount": 1}
            outputs[i].append(output)

    for output in outputs:
        req, _ = await payment.build_mint_req(wallet_handler, trustee_did, json.dumps(output), None)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
        res1 = json.loads(await ledger.submit_request(pool_handler, req))
        print(res1)
        assert res1['op'] == 'REPLY'

    sources = []
    for address in itertools.chain(*addresses):
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        source = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res)
        )[0]['source']
        sources.append(source)

    for source in sources:
        req, _ = await payment.build_payment_req(
            wallet_handler, trustee_did, json.dumps([source]), json.dumps([{"recipient": address0, "amount": 1}]), None
        )
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        assert res['op'] == 'REPLY'

    # default check
    req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address0)
    res1 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    print(res1)
    assert json.loads(res1)['op'] == 'REPLY'
    source1 = json.loads(
        await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res1)
    )[0]['source']
    print(source1)

    # check state proof reading and from feature
    outputs1 = [host.run('systemctl stop indy-node') for host in hosts[:-1]]
    print(outputs1)
    req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address0)  # TODO add from
    res2 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    print(res2)
    assert json.loads(res2)['op'] == 'REPLY'
    source2 = json.loads(
        await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res2)
    )[0]['source']
    print(source2)

    outputs2 = [host.run('systemctl start indy-node') for host in hosts[:-1]]
    print(outputs2)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
async def test_misc_2164(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee
    target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')

    # send valid request
    res1 = await send_nym(pool_handler, wallet_handler, trustee_did, target_did, target_vk)
    assert res1['op'] == 'REPLY'

    # block traffic between Node2, Node3, Node4 and a client
    for i in range(3, 6):
        for t in ['INPUT', 'OUTPUT']:
            p1 = subprocess.Popen(
                ['echo', '123456'],
                stdout=subprocess.PIPE
            )
            p2 = subprocess.Popen(
                ['sudo', '-S', 'iptables', '-A', '{}'.format(t), '-s', '10.0.0.{}'.format(i), '-j', 'DROP'],
                stdin=p1.stdout,
                stdout=subprocess.PIPE
            )
            p1.stdout.close()
            out, err = p2.communicate()
            assert err is None

    # unblock traffic between Node2 and client
    for t in ['INPUT', 'OUTPUT']:
        # input from Node2 to client is already unblocked here (can receive), but output is still blocked (cannot send)
        if t == 'OUTPUT':
            # send invalid request
            res2 = await send_nym(pool_handler, wallet_handler, trustee_did, target_did, target_vk)
            assert res2['op'] == 'REJECT'

        p1 = subprocess.Popen(
            ['echo', '123456'],
            stdout=subprocess.PIPE
        )
        p2 = subprocess.Popen(
            ['sudo', '-S', 'iptables', '-D', '{}'.format(t), '-s', '10.0.0.3', '-j', 'DROP'],
            stdin=p1.stdout,
            stdout=subprocess.PIPE
        )
        p1.stdout.close()
        out, err = p2.communicate()
        assert err is None

    # send valid request
    res3 = await send_nym(pool_handler, wallet_handler, trustee_did, target_did, None, None, 'STEWARD')
    assert res3['op'] == 'REPLY'

    # unblock traffic between Node3, Node4 and a client
    for i in range(4, 6):
        for t in ['INPUT', 'OUTPUT']:
            p1 = subprocess.Popen(
                ['echo', '123456'],
                stdout=subprocess.PIPE
            )
            p2 = subprocess.Popen(
                ['sudo', '-S', 'iptables', '-D', '{}'.format(t), '-s', '10.0.0.{}'.format(i), '-j', 'DROP'],
                stdin=p1.stdout,
                stdout=subprocess.PIPE
            )
            p1.stdout.close()
            out, err = p2.communicate()
            assert err is None


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
async def test_misc_2112(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
):
    client = docker.from_env()
    trustee_did, _ = get_default_trustee
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=25)
    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    client.networks.list(names=['indy-test-automation-network'])[0].disconnect('node4')
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=100)
    for i in range(5):
        await asyncio.sleep(15)
        client.networks.list(names=['indy-test-automation-network'])[0].connect('node4')
        client.networks.list(names=['indy-test-automation-network'])[0].disconnect('node4')
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=200)
    client.networks.list(names=['indy-test-automation-network'])[0].connect('node4')
    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, timeout=180)


@pytest.mark.asyncio
async def test_misc_is_1284():
    pool_handle, _ = await pool_helper(path_to_genesis='../buildernet_genesis')
    wallet_handle, _, _ = await wallet_helper()
    builder_did, builder_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': str('I22aXMicTRh1ILWojMVJMvvzznlFwVUj')}))
    res = await send_nym(
        pool_handle, wallet_handle, builder_did, 'NSNGwB2MK7WVoG7CLmHhfy', '~PRDkZn9HMSL2MUWKFJLpi9', None, 'STEWARD'
    )
    print(res)
    assert res['op'] == 'REJECT'


@pytest.mark.asyncio
async def test_misc_2171(
        docker_setup_and_teardown, payment_init, pool_handler, wallet_handler, get_default_trustee,
        initial_token_minting
):
    libsovtoken_payment_method = 'sov'
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    other_did, other_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    trustee_did_second, trustee_vk_second = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    trustee_did_third, trustee_vk_third = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_second, trustee_vk_second, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_third, trustee_vk_third, None, 'TRUSTEE')
    address = initial_token_minting
    fees = {'off_ledger_nym': 100 * 100000}
    req = await payment.build_set_txn_fees_req(
        wallet_handler, trustee_did, libsovtoken_payment_method, json.dumps(fees)
    )
    req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_second, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_third, req)
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
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
                                                               'metadata': {'fees': 'off_ledger_nym'}
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
    req, _ = await payment.build_get_payment_sources_request(wallet_handler, new_did, address)
    res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, new_did, req)
    source = json.loads(await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res))[0]['source']
    req5 = await ledger.build_nym_request(new_did, new_did, new_vk, 'my own did', None)
    req5, _ = await payment.add_request_fees(
        wallet_handler, new_did, req5, json.dumps([source]), json.dumps(
            [{'recipient': address, 'amount': 900 * 100000}]
        ), None
    )
    res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, new_did, req5))
    print(res5)
    assert res5['op'] == 'REPLY'
    req = await ledger.build_get_auth_rule_request(None, None, None, None, None, None)
    res6 = json.loads(await ledger.submit_request(pool_handler, req))
    print(res6)


@pytest.mark.asyncio
async def test_misc_2173(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee
    off_did, off_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    e_did, e_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    test_did, test_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(pool_handler, wallet_handler, trustee_did, off_did, off_vk, 'No role', None)
    assert res['op'] == 'REPLY'
    res = await send_nym(pool_handler, wallet_handler, trustee_did, e_did, e_vk, 'Endorser', 'ENDORSER')
    assert res['op'] == 'REPLY'

    req00 = await ledger.build_nym_request(off_did, test_did, test_vk, 'Alias 1', None)
    res00 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, off_did, req00))
    assert res00['op'] == 'REJECT'
    req0 = await ledger.build_nym_request(off_did, test_did, test_vk, 'Alias 1', None)
    req0 = await ledger.append_request_endorser(req0, e_did)
    req0 = await ledger.multi_sign_request(wallet_handler, off_did, req0)
    req0 = await ledger.multi_sign_request(wallet_handler, e_did, req0)
    res0 = json.loads(await ledger.submit_request(pool_handler, req0))
    print(res0)
    assert res0['op'] == 'REPLY'

    schema_id, schema_json = await anoncreds.issuer_create_schema(off_did, 'Schema 1', '0.1', json.dumps(['a1', 'a2']))
    req11 = await ledger.build_schema_request(off_did, schema_json)
    res11 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, off_did, req11))
    assert res11['op'] == 'REJECT'
    req1 = await ledger.build_schema_request(off_did, schema_json)
    req1 = await ledger.append_request_endorser(req1, e_did)
    req1 = await ledger.multi_sign_request(wallet_handler, off_did, req1)
    req1 = await ledger.multi_sign_request(wallet_handler, e_did, req1)
    res1 = json.loads(await ledger.submit_request(pool_handler, req1))
    print(res1)
    assert res1['op'] == 'REPLY'

    await asyncio.sleep(3)
    res = json.dumps(await get_schema(pool_handler, wallet_handler, trustee_did, schema_id))
    schema_id, schema_json = await ledger.parse_get_schema_response(res)
    cred_def_id, cred_def_json = await anoncreds.issuer_create_and_store_credential_def(
        wallet_handler, off_did, schema_json, 'cred def tag', None, json.dumps({'support_revocation': True})
    )
    req22 = await ledger.build_cred_def_request(off_did, cred_def_json)
    res22 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, off_did, req22))
    assert res22['op'] == 'REJECT'
    req2 = await ledger.build_cred_def_request(off_did, cred_def_json)
    req2 = await ledger.append_request_endorser(req2, e_did)
    req2 = await ledger.multi_sign_request(wallet_handler, off_did, req2)
    req2 = await ledger.multi_sign_request(wallet_handler, e_did, req2)
    res2 = json.loads(await ledger.submit_request(pool_handler, req2))
    print(res2)
    assert res2['op'] == 'REPLY'

    tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
    tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
    revoc_reg_id, revoc_reg_def_json, revoc_reg_entry_json = await anoncreds.issuer_create_and_store_revoc_reg(
        wallet_handler, off_did, None, 'revoc reg tag', cred_def_id, json.dumps(
            {'max_cred_num': 100, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}
        ), tails_writer_handle
    )
    req33 = await ledger.build_revoc_reg_def_request(off_did, revoc_reg_def_json)
    res33 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, off_did, req33))
    assert res33['op'] == 'REJECT'
    req3 = await ledger.build_revoc_reg_def_request(off_did, revoc_reg_def_json)
    req3 = await ledger.append_request_endorser(req3, e_did)
    req3 = await ledger.multi_sign_request(wallet_handler, off_did, req3)
    req3 = await ledger.multi_sign_request(wallet_handler, e_did, req3)
    res3 = json.loads(await ledger.submit_request(pool_handler, req3))
    print(res3)
    assert res3['op'] == 'REPLY'

    req44 = await ledger.build_revoc_reg_entry_request(off_did, revoc_reg_id, 'CL_ACCUM', revoc_reg_entry_json)
    res44 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, off_did, req44))
    assert res44['op'] == 'REJECT'
    req4 = await ledger.build_revoc_reg_entry_request(off_did, revoc_reg_id, 'CL_ACCUM', revoc_reg_entry_json)
    req4 = await ledger.append_request_endorser(req4, e_did)
    req4 = await ledger.multi_sign_request(wallet_handler, off_did, req4)
    req4 = await ledger.multi_sign_request(wallet_handler, e_did, req4)
    res4 = json.loads(await ledger.submit_request(pool_handler, req4))
    print(res4)
    assert res4['op'] == 'REPLY'
