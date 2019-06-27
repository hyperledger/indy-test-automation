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


# logger = logging.getLogger(__name__)
# logging.basicConfig(level=0, format='%(asctime)s %(message)s')


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
async def test_misc_state_proof():
    await pool.set_protocol_version(2)
    timestamp0 = int(time.time())
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    random_did = random_did_and_json()[0]
    await send_nym(pool_handle, wallet_handle, trustee_did, random_did)
    await send_attrib(pool_handle, wallet_handle, trustee_did, random_did, None, json.dumps({'key': 'value'}), None)
    schema_id, _ = await send_schema(pool_handle, wallet_handle, trustee_did, random_string(10), '1.0',
                                     json.dumps([random_string(1), random_string(2), random_string(3)]))
    await asyncio.sleep(1)
    res = json.dumps(await get_schema(pool_handle, wallet_handle, trustee_did, schema_id))
    schema_id, schema_json = await ledger.parse_get_schema_response(res)
    cred_def_id, _, _ = await send_cred_def(pool_handle, wallet_handle, trustee_did, schema_json, random_string(3),
                                            None, json.dumps({'support_revocation': True}))
    revoc_reg_def_id, _, _, res1 = await send_revoc_reg_entry(pool_handle, wallet_handle, trustee_did, 'CL_ACCUM',
                                                              random_string(3), cred_def_id,
                                                              json.dumps({'max_cred_num': 1,
                                                                          'issuance_type': 'ISSUANCE_BY_DEFAULT'}))
    timestamp1 = int(time.time())

    # uncomment to check freshness state proof reading
    # await asyncio.sleep(600)

    hosts = [testinfra.get_host('docker://node' + str(i)) for i in range(1, 8)]
    print(hosts)
    outputs0 = [host.run('systemctl stop indy-node') for host in hosts[:-1]]
    print(outputs0)
    try:
        req1 = await ledger.build_get_nym_request(None, random_did)
        res1 = json.loads(await ledger.submit_request(pool_handle, req1))

        req2 = await ledger.build_get_attrib_request(None, random_did, 'key', None, None)
        res2 = json.loads(await ledger.submit_request(pool_handle, req2))

        req3 = await ledger.build_get_schema_request(None, schema_id)
        res3 = json.loads(await ledger.submit_request(pool_handle, req3))

        req4 = await ledger.build_get_cred_def_request(None, cred_def_id)
        res4 = json.loads(await ledger.submit_request(pool_handle, req4))

        req5 = await ledger.build_get_revoc_reg_def_request(None, revoc_reg_def_id)
        res5 = json.loads(await ledger.submit_request(pool_handle, req5))

        # consensus is impossible with timestamp0 here! IS-1263
        req6 = await ledger.build_get_revoc_reg_request(None, revoc_reg_def_id, timestamp1)
        res6 = json.loads(await ledger.submit_request(pool_handle, req6))

        # consensus is impossible with (timestamp0, timestamp1) here! IS-1264
        req7 = await ledger.build_get_revoc_reg_delta_request(None, revoc_reg_def_id, None, timestamp1)
        res7 = json.loads(await ledger.submit_request(pool_handle, req7))
    finally:
        outputs1 = [host.run('systemctl start indy-node') for host in hosts[:-1]]
        print(outputs1)

    assert res1['result']['seqNo'] is not None
    assert res2['result']['seqNo'] is not None
    assert res3['result']['seqNo'] is not None
    assert res4['result']['seqNo'] is not None
    assert res5['result']['seqNo'] is not None
    assert res6['result']['seqNo'] is not None
    assert res7['result']['seqNo'] is not None

    print(res1)
    print(res2)
    print(res3)
    print(res4)
    print(res5)
    print(res6)
    print(res7)


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
    pool_handle, _ = await pool_helper(path_to_genesis='../aws_genesis')
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
    for i in range(100):
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
    print('\n{}:\n{}'.format(amount, res))
    assert res['op'] == 'REQNACK'
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
