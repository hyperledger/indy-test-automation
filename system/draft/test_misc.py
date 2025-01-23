import pytest
from system.utils import *
from system.utils import create_and_store_did, pool_helper, wallet_helper
import testinfra
import subprocess
import numpy as np
from random import randrange as rr
from random import sample, choice
from datetime import datetime, timedelta, timezone
import hashlib
from hypothesis import settings, Verbosity, given, strategies
import pprint
import docker
from system.docker_setup import client, pool_builder, pool_starter,\
    DOCKER_BUILD_CTX_PATH, DOCKER_IMAGE_NAME, NETWORK_NAME


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
async def test_misc_get_nonexistent(docker_setup_and_teardown):
    timestamp0 = int(time.time())
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    submitter_did, submitter_vk = await create_and_store_did(wallet_handle, seed='000000000000000000000000Trustee1')
    timestamp1 = int(time.time())

    res1 = json.dumps(
        await get_schema(pool_handle, wallet_handle, submitter_did, 'WKWN6U6XKTFxJBC3mB7Pdo:2:schema1:1.0')
    )
    res2 = json.dumps(
        await get_cred_def(pool_handle, wallet_handle, submitter_did, '3VTSJXBKw2DBjfaJt4eS1X:3:CL:685:TAG')
    )
    res3 = json.dumps(
        await get_revoc_reg_def(
            pool_handle, wallet_handle, submitter_did,
            'RgTvEeKFSxd2Fcsxh42k9T:4:RgTvEeKFSxd2Fcsxh42k9T:3:CL:689:cred_def_tag:CL_ACCUM:revoc_def_tag'
        )
    )
    res4 = json.dumps(
        await get_revoc_reg(
            pool_handle, wallet_handle, submitter_did,
            'RgTvEeKFSxd2Fcsxh42k9T:4:RgTvEeKFSxd2Fcsxh42k9T:3:CL:689:cred_def_tag:CL_ACCUM:revoc_def_tag',
            timestamp0
        )
    )
    res5 = json.dumps(
        await get_revoc_reg_delta(
            pool_handle, wallet_handle, submitter_did,
            'RgTvEeKFSxd2Fcsxh42k9T:4:RgTvEeKFSxd2Fcsxh42k9T:3:CL:689:cred_def_tag:CL_ACCUM:revoc_def_tag',
            timestamp0, timestamp1
        )
    )

    with pytest.raises(LedgerNotFound):
        await ledger.parse_get_schema_response(res1)

    with pytest.raises(LedgerNotFound):
        await ledger.parse_get_cred_def_response(res2)

    with pytest.raises(LedgerNotFound):
        await ledger.parse_get_revoc_reg_def_response(res3)

    with pytest.raises(LedgerNotFound):
        await ledger.parse_get_revoc_reg_response(res4)

    with pytest.raises(LedgerNotFound):
        await ledger.parse_get_revoc_reg_delta_response(res5)


@pytest.mark.skip()
@pytest.mark.asyncio
async def test_misc_wallet():
    wallet_handle, _, _ = await wallet_helper('abc', 'abc', 'ARGON2I_MOD')
    await create_and_store_did(wallet_handle, seed='000000000000000000000000Trustee1')


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
async def test_misc_get_txn_by_seqno(docker_setup_and_teardown):
    pool_handle, _ = await pool_helper()
    req = await ledger.build_get_txn_request(None, None, 1)
    res = json.loads(await ledger.submit_request(pool_handle, req))
    print(res)
    assert res['result']['seqNo'] == 1


@pytest.mark.asyncio
async def test_misc_stn_slowness():
    schema_timings = []
    cred_def_timings = []
    nodes = [
        'NodeTwinPeek',
        'RFCU',
        'australia',
        'brazil',
        'canada',
        'england',
        'ibmTest',
        'korea',
        'lab10',
        'singapore',
        'virginia',
        'vnode1',
        'xsvalidatorec2irl'
    ]
    for i in range(10):
        for node in nodes:
            pool_handle, _ = await pool_helper(path_to_genesis='../stn_genesis', node_list=[node, ])

            t1 = time.perf_counter()
            req1 = await ledger.build_get_schema_request(
                None, 'Rvk7x5oSFwoLWZK8rM1Anf:2:Passport Office1539941790480:1.0'
            )
            schema_build_time = time.perf_counter() - t1
            await ledger.submit_request(pool_handle, req1)
            schema_submit_time = time.perf_counter() - t1 - schema_build_time
            schema_timings.append(schema_submit_time)
            print(
                'ITERATION: ', i, '\t',
                'NODE: ', node, '\t',
                'SCHEMA BUILD TIME: ', schema_build_time, '\t',
                'SCHEMA SUBMIT TIME: ', schema_submit_time
            )

            t2 = time.perf_counter()
            req2 = await ledger.build_get_cred_def_request(None, 'Rvk7x5oSFwoLWZK8rM1Anf:3:CL:9726:tag1')
            cred_def_build_time = time.perf_counter() - t2
            await ledger.submit_request(pool_handle, req2)
            cred_def_submit_time = time.perf_counter() - t2 - cred_def_build_time
            cred_def_timings.append(cred_def_submit_time)
            print(
                'ITERATION: ', i, '\t',
                'NODE: ', node, '\t',
                'CRED DEF BUILD TIME: ', cred_def_build_time, '\t',
                'CRED DEF SUBMIT TIME: ', cred_def_submit_time
            )

    print('SCHEMA_SUBMIT_AVG', np.average(schema_timings))
    print('CRED_DEF_SUBMIT_AVG', np.average(cred_def_timings))

    assert np.mean(schema_timings) < 1.5
    assert np.mean(cred_def_timings) < 0.5


@pytest.mark.asyncio
async def test_new_role(docker_setup_and_teardown):
    # INDY-1916 / IS-1123
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    role_under_test = 'NETWORK_MONITOR'

    did1, vk1 = await create_and_store_did(wallet_handle)
    did2, vk2 = await create_and_store_did(wallet_handle)
    did3, vk3 = await create_and_store_did(wallet_handle)
    did4, vk4 = await create_and_store_did(wallet_handle)
    did5, vk5 = await create_and_store_did(wallet_handle)

    trustee_did, trustee_vk = await create_and_store_did(
        wallet_handle, seed='000000000000000000000000Trustee1'
    )
    steward_did, steward_vk = await create_and_store_did(
        wallet_handle, seed='000000000000000000000000Steward1'
    )
    anchor_did, anchor_vk = await create_and_store_did(wallet_handle)
    await send_nym(pool_handle, wallet_handle, trustee_did, anchor_did, anchor_vk, 'trust anchor', 'TRUST_ANCHOR')
    user_did, user_vk = await create_and_store_did(wallet_handle)
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
async def test_misc_pool_config(docker_setup_and_teardown):
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    trustee_did, trustee_vk = await create_and_store_did(
        wallet_handle, seed='000000000000000000000000Trustee1'
    )
    new_steward_did, new_steward_vk = await create_and_store_did(wallet_handle)
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
            }
    )
    req = await ledger.build_node_request(new_steward_did, 'koKn32jREPYR642DQsFftPoCkTf3XCPcfvc3x9RhRK7', data)
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, new_steward_did, req))
    assert res1['op'] == 'REPLY'

    req = await ledger.build_pool_config_request(trustee_did, True, False)
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    assert res2['op'] == 'REPLY'

    res3 = await send_nym(pool_handle, wallet_handle, trustee_did, random_did_and_json()[0])
    assert res3['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_error_handling(docker_setup_and_teardown, pool_handler, wallet_handler):
    d, vk = await create_and_store_did(wallet_handler)
    with pytest.raises(CommonInvalidStructure) as e1:
        await anoncreds.issuer_create_schema(d, random_string(5), random_string(5), json.dumps([{}]))
    with pytest.raises(CommonInvalidStructure) as e2:
        await crypto.get_key_metadata(wallet_handler, random_string(10))
    with pytest.raises(CommonInvalidStructure) as e3:
        await create_and_store_did(wallet_handler, json.dumps({'did': ''}))
    with pytest.raises(WalletItemNotFound) as e4:
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, '3fyKjNLV6foqDxoEbBiQhY', json.dumps({}))
    with pytest.raises(WalletInvalidHandle) as e5:
        await non_secrets.add_wallet_record(0, random_string(1), random_string(2), random_string(3), json.dumps({}))
    with pytest.raises(CommonInvalidParam3) as e6:
        await pairwise.create_pairwise(wallet_handler, '', '', None)
    with pytest.raises(CommonIOError) as e7:
        await pool.create_pool_ledger_config('docker', None)  # already exists
    with pytest.raises(CommonInvalidStructure) as e8:
        await wallet.create_wallet(json.dumps({}), json.dumps({}))


@pytest.mark.asyncio
async def test_misc_vi_freshness(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    # INDY-1928
    trustee_did, _ = get_default_trustee
    req = await ledger.build_get_validator_info_request(trustee_did)
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    res = json.loads(sample(res.items(), 1)[0][1])
    assert res['result']['data']['Node_info']['Freshness_status']['0']['Has_write_consensus'] is True
    assert datetime.strftime(datetime.now(tz=timezone.utc), '%Y-%m-%d %H:%M') in\
        res['result']['data']['Node_info']['Freshness_status']['0']['Last_updated_time']


@pytest.mark.parametrize('role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', 'NETWORK_MONITOR'])
@pytest.mark.asyncio
async def test_misc_permission_error_messages(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, role
):
    # INDY-1963
    trustee_did, _ = get_default_trustee
    did1, vk1 = await create_and_store_did(wallet_handler)
    did2, vk2 = await create_and_store_did(wallet_handler)
    await send_nym(pool_handler, wallet_handler, trustee_did, did1, vk1, None, role)

    res1 = await send_nym(pool_handler, wallet_handler, trustee_did, did1, vk2, None, None)
    assert (res1['op'] == 'REJECT') and\
           (res1['reason'].find('can not touch verkey field since only the owner can modify it') is not -1)

    await send_nym(pool_handler, wallet_handler, trustee_did, did1, None, None, '')

    res2 = await send_nym(pool_handler, wallet_handler, did1, did2, vk2, None, None)
    assert (res2['op'] == 'REJECT') and\
           (res2['reason'].find('Rule for this action is') is not -1)


@pytest.mark.asyncio
async def test_misc_indy_1933(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    # INDY-1933
    trustee_did, _ = get_default_trustee
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
    nodes = ['node2', 'node3']
    outputs = [
        subprocess.check_call(
            ['docker', 'exec', '-d', node, 'stress', '-c', '1', '-i', '1', '-m', '1']
        ) for node in nodes
    ]
    print(outputs)
    for i in range(200):
        await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    dict_results = {key: json.loads(results[key]) for key in results}
    print(dict_results)
    assert all([dict_results[key]['op'] == 'REPLY' for key in dict_results])


@pytest.mark.asyncio
async def test_misc_is_1158(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    issuer_did, _ = get_default_trustee
    prover_did, prover_vk = await create_and_store_did(wallet_handler)
    schema_id, s_res = await send_schema(
        pool_handler, wallet_handler, issuer_did, random_string(5), '1.0', json.dumps(["hash", "enc", "raw"])
    )
    assert s_res['op'] == 'REPLY'
    res = await get_schema(pool_handler, wallet_handler, issuer_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, cred_def_json, c_res = await send_cred_def(
        pool_handler, wallet_handler, issuer_did, schema_json, random_string(3), None, json.dumps(
            {'support_revocation': False}
        )
    )
    assert c_res['op'] == 'REPLY'
    master_secret_id = await anoncreds.prover_create_master_secret(wallet_handler, None)
    cred_offer = await anoncreds.issuer_create_credential_offer(wallet_handler, cred_def_id)
    assert cred_offer is not None
    cred_req, cred_req_metadata = await anoncreds.prover_create_credential_req(
        wallet_handler, prover_did, cred_offer, cred_def_json, master_secret_id
    )
    cred_values = json.dumps(
        {
            "hash": {"raw": random_string(10), "encoded": "5944657099558967239210949205008160769251991705004233"},
            "enc": {"raw": "100", "encoded": "594967239210949258394887428692050081607692519917050033"},
            "raw": {"raw": random_string(10), "encoded": "59446570995589672392109492583948874286920500816"}
        }
    )
    cred_json, _, _ = await anoncreds.issuer_create_credential(
        wallet_handler, cred_offer, cred_req, cred_values, None, None
    )
    assert cred_json is not None


@pytest.mark.asyncio
async def test_misc_audit_ledger(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    node_to_stop = '7'
    host = testinfra.get_host('ssh://node'+node_to_stop)
    trustee_did, _ = get_default_trustee
    for i in range(25):
        steward_did, steward_vk = await create_and_store_did(wallet_handler)
        await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, 'STEWARD')
        req1 = await ledger.build_node_request(
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
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req1)
        req3 = await ledger.build_pool_config_request(trustee_did, True, False)
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req3)
    output = host.check_output('systemctl stop indy-node')
    print(output)
    for i in range(25):
        steward_did, steward_vk = await create_and_store_did(wallet_handler)
        await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, 'STEWARD')
        req1 = await ledger.build_node_request(
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
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req1)
        req3 = await ledger.build_pool_config_request(trustee_did, True, False)
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req3)
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
async def test_misc_is_1201(
        pool_handler, wallet_handler, get_default_trustee, txn_type, action, field, old, new, constraint
):
    trustee_did, _ = get_default_trustee
    req = await ledger.build_auth_rule_request(trustee_did, txn_type, action, field, old, new, constraint)
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res)
    assert res['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_nodes_adding(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    steward_did, steward_vk = await create_and_store_did(wallet_handler)
    await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, 'STEWARD')
    req1 = await ledger.build_node_request(
        steward_did, steward_vk, json.dumps(
            {
                'alias': random_string(5),
                'client_ip': '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                'client_port': rr(1, 32767),
                'node_ip': '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                'node_port': rr(1, 32767),
                'services': ['VALIDATOR']
            }
        )
    )
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req1))
    assert res1['op'] == 'REPLY'
    req2 = await ledger.build_node_request(
        steward_did, steward_vk, json.dumps(
            {
                'alias': random_string(5),
                'client_ip': '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                'client_port': rr(1, 32767),
                'node_ip': '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255)),
                'node_port': rr(1, 32767),
                'services': ['VALIDATOR']
            }
        )
    )
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req2))
    assert res2['op'] == 'REJECT'


@pytest.mark.skip('deprecated')
@pytest.mark.asyncio
async def test_misc_indy_1554_can_write_true(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await create_and_store_did(wallet_handler)
    await send_nym(pool_handler, wallet_handler, trustee_did, new_did, new_vk, None, None)

    schema_id, _ = await send_schema(
        pool_handler, wallet_handler, new_did, 'schema1', '1.0', json.dumps(["age", "sex", "height", "name"])
    )
    res = await ensure_get_something(get_schema, pool_handler, wallet_handler, new_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, _, res = await send_cred_def(
        pool_handler, wallet_handler, new_did, schema_json, 'cred_def_tag', 'CL', json.dumps(
            {
                'support_revocation': True
            }
        )
    )
    revoc_reg_def_id, _, _, res1 = await send_revoc_reg_entry(
        pool_handler, wallet_handler, new_did, 'CL_ACCUM', 'revoc_def_tag', cred_def_id, json.dumps(
            {
                'max_cred_num': 1,
                'issuance_type': 'ISSUANCE_BY_DEFAULT'
            }
        )
    )
    print(res1)
    revoc_reg_def_id, _, _, res9 = await send_revoc_reg_entry(
        pool_handler, wallet_handler, trustee_did, 'CL_ACCUM', 'another_revoc_def_tag', cred_def_id, json.dumps(
            {
                'max_cred_num': 1,
                'issuance_type': 'ISSUANCE_BY_DEFAULT'
            }
        )
    )
    print(res9)

    assert res1['op'] == 'REPLY'
    assert res9['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_indy_1554_can_write_false(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await create_and_store_did(wallet_handler)
    t_did, t_vk = await create_and_store_did(wallet_handler)
    await send_nym(pool_handler, wallet_handler, trustee_did, new_did, new_vk, None, None)
    await send_nym(pool_handler, wallet_handler, trustee_did, t_did, t_vk, None, 'TRUSTEE')

    schema_id, _ = await send_schema(
        pool_handler, wallet_handler, trustee_did, 'schema1', '1.0', json.dumps(["age", "sex", "height", "name"])
    )
    res = await ensure_get_something(get_schema, pool_handler, wallet_handler, new_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, _, res = await send_cred_def(
        pool_handler, wallet_handler, trustee_did, schema_json, 'cred_def_tag', 'CL', json.dumps(
            {'support_revocation': True}
        )
    )

    # Creation by None role - FAIL
    revoc_reg_def_id1, revoc_reg_def_json1, revoc_reg_entry_json1, res1 = await send_revoc_reg_entry(
        pool_handler, wallet_handler, new_did, 'CL_ACCUM', 'revoc_def_tag', cred_def_id, json.dumps(
            {
                'max_cred_num': 1,
                'issuance_type': 'ISSUANCE_BY_DEFAULT'
            }
        )
    )

    # Creation by Trustee role - PASS
    revoc_reg_def_id2, revoc_reg_def_json2, revoc_reg_entry_json2, res2 = await send_revoc_reg_entry(
        pool_handler, wallet_handler, trustee_did, 'CL_ACCUM', 'another_revoc_def_tag', cred_def_id, json.dumps(
            {
                'max_cred_num': 1,
                'issuance_type': 'ISSUANCE_BY_DEFAULT'
            }
        )
    )

    # Editing by None role and not owner both entities
    req = await ledger.build_revoc_reg_def_request(new_did, revoc_reg_def_json2)
    res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, new_did, req))
    req = await ledger.build_revoc_reg_entry_request(new_did, revoc_reg_def_id2, 'CL_ACCUM', revoc_reg_entry_json2)
    res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, new_did, req))

    # Editing by Trustee role and not owner both entities
    req = await ledger.build_revoc_reg_def_request(t_did, revoc_reg_def_json2)
    res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, t_did, req))
    req = await ledger.build_revoc_reg_entry_request(t_did, revoc_reg_def_id2, 'CL_ACCUM', revoc_reg_entry_json2)
    res6 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, t_did, req))

    # Editing by Trustee role and owner both entities
    req = await ledger.build_revoc_reg_def_request(trustee_did, revoc_reg_def_json2)
    res7 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    req = await ledger.build_revoc_reg_entry_request(trustee_did, revoc_reg_def_id2, 'CL_ACCUM', revoc_reg_entry_json2)
    res8 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))

    assert res1['op'] == 'REJECT'
    assert res2['op'] == 'REPLY'
    assert res3['op'] == 'REJECT'
    assert res4['op'] == 'REJECT'
    assert res5['op'] == 'REPLY'
    assert res6['op'] == 'REJECT'
    assert res7['op'] == 'REPLY'
    assert res8['op'] == 'REJECT'


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
async def test_misc_is_1202(
        docker_setup_and_teardown_module, pool_handler, wallet_handler, get_default_trustee,
        submitter_did, txn_type, action, field, old_value, new_value
):
    trustee_did, _ = get_default_trustee
    req = await ledger.build_get_auth_rule_request(submitter_did, txn_type, action, field, old_value, new_value)
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print('\n', res)
    assert res['op'] == 'REPLY'


@pytest.mark.asyncio
async def test_misc_is_1085(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    res = await get_nym(pool_handler, wallet_handler, trustee_did, trustee_did)
    print(res)


@pytest.mark.asyncio
async def test_misc_indy_2022(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
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
    await ensure_pool_is_in_sync()


@pytest.mark.skip('async one works now')
@settings(verbosity=Verbosity.debug, deadline=2000.0, max_examples=100)
@given(
    h_text=strategies.text(alphabet=strategies.characters(whitelist_categories=('L', 'Sc')), min_size=5, max_size=50),
    h_first_number=strategies.integers(min_value=0, max_value=999),
    h_last_number=strategies.integers(min_value=999, max_value=99999)
)
def test_misc_hypothesis_sync(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
        h_text, h_first_number, h_last_number
):
    trustee_did, _ = get_default_trustee
    res = run_async_method(
        send_schema, pool_handler, wallet_handler, trustee_did, h_text, str(h_first_number)+'.'+str(h_last_number), json.dumps(
            [random_string(10), random_string(25)]
        )
    )
    print(res[1])
    assert res[1]['op'] == 'REPLY'


@settings(verbosity=Verbosity.debug, deadline=2000.0, max_examples=100)
@given(
    h_text=strategies.text(alphabet=strategies.characters(whitelist_categories=('L', 'Sc')), min_size=5, max_size=50),
    h_first_number=strategies.integers(min_value=0, max_value=999),
    h_last_number=strategies.integers(min_value=999, max_value=99999)
)
@pytest.mark.asyncio
async def test_misc_hypothesis_async(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
        h_text, h_first_number, h_last_number
):
    trustee_did, _ = get_default_trustee
    res = await send_schema(
        pool_handler, wallet_handler, trustee_did, h_text, str(h_first_number)+'.'+str(h_last_number), json.dumps(
            [random_string(10), random_string(25)]
        )
    )
    print(res[1])
    assert res[1]['op'] == 'REPLY'


@pytest.mark.parametrize('role_under_test', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', 'NETWORK_MONITOR'])
@pytest.mark.asyncio
# INDY-2033
async def test_misc_role_changing(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, role_under_test
):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await create_and_store_did(wallet_handler)
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
# INDY-1720
async def test_misc_vc_processing(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    primary1, alias1, target_did1 = await get_primary(pool_handler, wallet_handler, trustee_did)
    await demote_node(pool_handler, wallet_handler, trustee_did, alias1, target_did1)
    primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
    assert primary2 != primary1
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=100, timeout=100)
    await promote_node(pool_handler, wallet_handler, trustee_did, alias1, target_did1)
    primary3 = await wait_until_vc_is_done(primary2, pool_handler, wallet_handler, trustee_did)
    assert primary3 != primary2
    output = testinfra.get_host('ssh://node{}'.format(primary3)).check_output('systemctl stop indy-node')
    print(output)
    primary4 = await wait_until_vc_is_done(primary3, pool_handler, wallet_handler, trustee_did)
    assert primary4 != primary3
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=100, timeout=100)
    output = testinfra.get_host('ssh://node{}'.format(primary3)).check_output('systemctl start indy-node')
    print(output)
    await ensure_pool_is_in_sync()
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)


@pytest.mark.asyncio
# IS-1237
async def test_misc_auth_rule_special_case(docker_setup_and_teardown, get_default_trustee):
    print()
    trustee_did, _ = get_default_trustee
    req1 = json.loads(
        await ledger.build_auth_rule_request(
            trustee_did, '1', 'ADD', 'role', '*', '', json.dumps(
                {
                    'constraint_id': 'ROLE',
                    'role': '*',
                    'sig_count': 1,
                    'need_to_be_owner': False,
                    'metadata': {}
                }
            )
        )
    )
    pprint.pprint(req1)
    req2 = json.loads(
        await ledger.build_auth_rule_request(
            trustee_did, '1', 'EDIT', 'role', '*', None, json.dumps(
                {
                    'constraint_id': 'ROLE',
                    'role': '*',
                    'sig_count': 1,
                    'need_to_be_owner': False,
                    'metadata': {}
                }
            )
        )
    )
    pprint.pprint(req2)


@pytest.mark.asyncio
async def test_case_nym_special_case(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await create_and_store_did(wallet_handler)
    reader_did, _ = await create_and_store_did(wallet_handler)
    editor_did, editor_vk = await create_and_store_did(wallet_handler)
    res1 = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk)
    assert res1['op'] == 'REPLY'
    res2 = await send_nym(pool_handler, wallet_handler, trustee_did, new_did)
    print(res2)
    res3 = await send_nym(pool_handler, wallet_handler, editor_did, new_did)
    print(res3)
    res4 = await get_nym(pool_handler, wallet_handler, reader_did, new_did)
    print(res4)


@settings(deadline=None, max_examples=100)
@given(
    target_alias=strategies.text(
        alphabet=strategies.characters(whitelist_categories=('L', 'N', 'S')), min_size=1, max_size=1000
    )
)
@pytest.mark.asyncio
async def test_misc_nym_alias(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, target_alias
):
    trustee_did, _ = get_default_trustee
    new_did, new_vk = await create_and_store_did(wallet_handler)
    res = await send_nym(pool_handler, wallet_handler, trustee_did, new_did, None, target_alias, None)
    assert res['op'] == 'REPLY'


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


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
# INDY-2164
async def test_misc_slow_pool_valid_response_test(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee
    target_did, target_vk = await create_and_store_did(wallet_handler)

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
# INDY-2112
async def test_misc_repeatable_ledger_status(
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
# IS-1284
async def test_misc_slow_pool_valid_response_live():
    SEC_PER_DAY = 24 * 60 * 60
    pool_handle, _ = await pool_helper(path_to_genesis='../buildernet_genesis')
    wallet_handle, _, _ = await wallet_helper()
    builder_did, builder_vk = await create_and_store_did(wallet_handle, seed='I22aXMicTRh1ILWojMVJMvvzznlFwVUj')
    req0 = await ledger.build_get_txn_author_agreement_request(builder_did, None)
    res_taa = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, builder_did, req0))

    req1 = await ledger.build_nym_request(
        builder_did, 'NSNGwB2MK7WVoG7CLmHhfy', '~PRDkZn9HMSL2MUWKFJLpi9', None, 'STEWARD'
    )
    req1 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req1, res_taa['result']['data']['text'], res_taa['result']['data']['version'], None, 'on_file',
        int(time.time()) // SEC_PER_DAY * SEC_PER_DAY
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, builder_did, req1))
    print(res)
    assert res['op'] == 'REJECT'


@pytest.mark.asyncio
#  INDY-2173
async def test_misc_endorser(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee
    off_did, off_vk = await create_and_store_did(wallet_handler)
    e_did, e_vk = await create_and_store_did(wallet_handler)
    test_did, test_vk = await create_and_store_did(wallet_handler)
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


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
#  IS-1306
async def test_misc_revocation_proof_without_timestamps(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    issuer_did, _ = get_default_trustee
    prover_did, prover_vk = await create_and_store_did(wallet_handler)

    schema_id, res1 = await send_schema(
        pool_handler, wallet_handler, issuer_did, 'Schema 1', '1.0', json.dumps(['name', 'age'])
    )
    assert res1['op'] == 'REPLY'
    await asyncio.sleep(1)
    res = await get_schema(pool_handler, wallet_handler, issuer_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, cred_def_json, res2 = await send_cred_def(
        pool_handler, wallet_handler, issuer_did, schema_json, 'Tag 1', None, json.dumps({'support_revocation': True})
    )
    assert res2['op'] == 'REPLY'
    revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json, res3 = await send_revoc_reg_def(
        pool_handler, wallet_handler, issuer_did, 'CL_ACCUM', 'Tag 2', cred_def_id, cred_def_json
    )
    assert res3['op'] == 'REPLY'

    master_secret_id = await anoncreds.prover_create_master_secret(wallet_handler, 'Master secret 1')
    cred_offer_json = await anoncreds.issuer_create_credential_offer(wallet_handler, cred_def_id)
    cred_req_json, cred_req_metadata_json = await anoncreds.prover_create_credential_req(
        wallet_handler, prover_did, cred_offer_json, cred_def_json, master_secret_id
    )
    cred_json, cred_revoc_id, revoc_reg_delta_json = await anoncreds.issuer_create_credential(
        wallet_handler, cred_offer_json, cred_req_json, json.dumps(
            {
                "name":
                    {
                        "raw": "Pyotr",
                        "encoded": "111"
                    },
                "age":
                    {
                        "raw": "99",
                        "encoded": "222"
                    }
            }
        ), None, None
    )
    cred_id = await anoncreds.prover_store_credential(
        wallet_handler, None, cred_req_metadata_json, cred_json, cred_def_json, revoc_reg_def_json
    )

    # proof request
    proof_request = json.dumps(
        {
            "nonce": "123432421212",
            "name": "proof_req_1",
            "version": "0.1",
            "requested_attributes":
                {
                    "attr1_referent":
                        {
                            "name": "name"
                        }
                },
            "requested_predicates":
                {
                    "predicate1_referent":
                        {
                            "name": "age", "p_type": ">=", "p_value": 18
                        }
                }
        }
    )
    credentials_json = await anoncreds.prover_get_credentials_for_proof_req(wallet_handler, proof_request)
    search_handle = await anoncreds.prover_search_credentials_for_proof_req(wallet_handler, proof_request, None)

    creds_for_attr1 = await anoncreds.prover_fetch_credentials_for_proof_req(
        search_handle, 'attr1_referent', 10
    )
    cred_for_attr1 = json.loads(creds_for_attr1)[0]['cred_info']

    creds_for_predicate1 = await anoncreds.prover_fetch_credentials_for_proof_req(
        search_handle, 'predicate1_referent', 10
    )
    cred_for_predicate1 = json.loads(creds_for_predicate1)[0]['cred_info']

    await anoncreds.prover_close_credentials_search_for_proof_req(search_handle)

    # primary proof
    requested_credentials_json = json.dumps(
        {
            "self_attested_attributes": {},
            "requested_attributes":
                {
                    "attr1_referent":
                        {
                            "cred_id": cred_for_attr1['referent'],
                            "revealed": True
                        }
                },
            "requested_predicates":
                {
                    "predicate1_referent":
                        {
                            "cred_id": cred_for_predicate1['referent']
                        }
                }
        }
    )

    schemas_json = json.dumps(
        {schema_id: json.loads(schema_json)}
    )
    cred_defs_json = json.dumps(
        {cred_def_id: json.loads(cred_def_json)}
    )

    proof = await anoncreds.prover_create_proof(
        wallet_handler, proof_request, requested_credentials_json, master_secret_id, schemas_json, cred_defs_json, '{}'
    )

    assert 'Pyotr' == json.loads(proof)['requested_proof']['revealed_attrs']['attr1_referent']['raw']
    assert await anoncreds.verifier_verify_proof(proof_request, proof, schemas_json, cred_defs_json, '{}', '{}')


@pytest.mark.asyncio
#  IS-1248
async def test_misc_modify_cred_def(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    issuer_did, _ = get_default_trustee

    schema_id, res1 = await send_schema(
        pool_handler, wallet_handler, issuer_did, 'Schema 1', '1.0', json.dumps(['name', 'age'])
    )
    assert res1['op'] == 'REPLY'
    await asyncio.sleep(1)

    res = await get_schema(pool_handler, wallet_handler, issuer_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, original_cred_def_json, res2 = await send_cred_def(
        pool_handler, wallet_handler, issuer_did, schema_json, 'Tag 1', None, json.dumps({'support_revocation': True})
    )
    assert res2['op'] == 'REPLY'

    rotated_cred_def_json = await anoncreds.issuer_rotate_credential_def_start(
        wallet_handler, cred_def_id, json.dumps({'support_revocation': True})
    )
    req = await ledger.build_cred_def_request(issuer_did, rotated_cred_def_json)
    res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, issuer_did, req))
    print(res3)
    assert res3['op'] == 'REPLY'
    await anoncreds.issuer_rotate_credential_def_apply(wallet_handler, cred_def_id)


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
# INDY-2211
async def test_misc_upgrade_ledger_with_old_auth_rule(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    """
    set up 1.1.50 sovrin + 1.9.0 node + 1.9.0 plenum + 1.0.0 plugins stable to fail
    (upgrade to 1.1.52 sovrin)

    set up 1.9.0~dev1014 node + 1.9.0~dev829 plenum master (no plugins env)
    (upgrade to 1.9.2~dev1061 node)

    set up 1.1.135 sovrin + 1.9.0~dev1014 node + 1.9.0~dev829 plenum + 1.0.0~dev59 plugins master (prod env)
    (upgrade to 1.1.136 sovrin)
    """

    # create extra node
    new_node = pool_starter(
        pool_builder(
            DOCKER_BUILD_CTX_PATH, DOCKER_IMAGE_NAME, 'new_node', NETWORK_NAME, 1
        )
    )[0]

    GENESIS_PATH = '/var/lib/indy/sandbox/'

    # put both genesis files
    print(new_node.exec_run(['mkdir', GENESIS_PATH], user='indy'))

    for _, prefix in enumerate(['pool', 'domain']):
        bits, stat = client.containers.get('node1'). \
            get_archive('{}{}_transactions_genesis'.format(GENESIS_PATH, prefix))
        assert new_node.put_archive(GENESIS_PATH, bits)

    new_ip = '10.0.0.6'
    PORT_1 = '9701'
    PORT_2 = '9702'
    new_alias = 'Node5'

    # initialize
    assert new_node.exec_run(
        ['init_indy_node', new_alias, new_ip, PORT_1, new_ip, PORT_2, '000000000000000000000000000node5'],
        user='indy'
    ).exit_code == 0

    # upgrade
    plenum_ver = '1.9.2~dev872'
    plenum_pkg = 'indy-plenum'
    node_ver = '1.9.2~dev1064'
    node_pkg = 'indy-node'
    sovrin_ver = '1.1.143'
    sovrin_pkg = 'sovrin'
    plugin_ver = '1.0.2~dev80'
    assert new_node.exec_run(
        ['apt', 'update'],
        user='root'
    ).exit_code == 0
    assert new_node.exec_run(
        ['apt', 'install',
         '{}={}'.format(sovrin_pkg, sovrin_ver),
         '{}={}'.format(node_pkg, node_ver),
         '{}={}'.format(plenum_pkg, plenum_ver),
         '-y'],
        user='root'
    ).exit_code == 0

    # # node only upgrade
    # assert new_node.exec_run(
    #     ['apt', 'update'],
    #     user='root'
    # ).exit_code == 0
    # assert new_node.exec_run(
    #     ['apt', 'install', '{}={}'.format(node_pkg, node_ver), '-y'],
    #     user='root'
    # ).exit_code == 0

    # start
    assert new_node.exec_run(
        ['systemctl', 'start', 'indy-node'],
        user='root'
    ).exit_code == 0

    trustee_did, _ = get_default_trustee
    steward_did, steward_vk = await create_and_store_did(wallet_handler)
    res = await send_nym(
        pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, 'Steward5', 'STEWARD'
    )
    assert res['op'] == 'REPLY'

    dests = [
        'Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv', '8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb',
        'DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya', '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA'
    ]
    init_time = 1
    name = 'upgrade'+'_'+sovrin_ver+'_'+datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
    action = 'start'
    _sha256 = hashlib.sha256().hexdigest()
    _timeout = 5
    docker_4_schedule = json.dumps(
        dict(
            {dest: datetime.strftime(
                datetime.now(tz=timezone.utc) + timedelta(minutes=init_time+i*5), '%Y-%m-%dT%H:%M:%S%z'
            ) for dest, i in zip(dests, range(len(dests)))}
        )
    )
    reinstall = False
    force = False

    # set rule for cred def adding
    req = await ledger.build_auth_rule_request(trustee_did, '102', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': '2',
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res1)
    assert res1['op'] == 'REPLY'

    # schedule pool upgrade
    version = '1.9.2.dev1064'  # overwrite for upgrade txn (for indy-node only)
    req = await ledger.build_pool_upgrade_request(
        trustee_did, name, sovrin_ver, action, _sha256, _timeout, docker_4_schedule, None, reinstall, force, sovrin_pkg
    )
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res2)
    assert res2['op'] == 'REPLY'

    # # INDY-2216
    # print(client.containers.list())
    #
    # for node in client.containers.list()[1:]:
    #     assert node.exec_run(
    #         ['systemctl', 'stop', 'indy-node'],
    #         user='root'
    #     ).exit_code == 0
    #
    # for node in client.containers.list()[1:]:
    #     assert node.exec_run(
    #         ['apt', 'update'],
    #         user='root'
    #     ).exit_code == 0
    #     print(
    #         node.exec_run(
    #             ['apt', 'install',
    #              '{}={}'.format(sovrin_pkg, sovrin_ver),
    #              '{}={}'.format(node_pkg, node_ver),
    #              '{}={}'.format(plenum_pkg, plenum_ver),
    #              '-y',
    #              '--allow-change-held-packages'],
    #             user='root'
    #         )
    #     )
    #
    # for node in client.containers.list()[1:]:
    #     assert node.exec_run(
    #         ['systemctl', 'start', 'indy-node'],
    #         user='root'
    #     ).exit_code == 0
    # # ------------------------

    # wait until upgrade is finished
    await asyncio.sleep(4*5*60)

    # add 5th node
    res3 = await send_node(
        pool_handler, wallet_handler, ['VALIDATOR'], steward_did, EXTRA_DESTS[0], new_alias,
        EXTRA_BLSKEYS[0], EXTRA_BLSKEY_POPS[0], new_ip, int(PORT_2), new_ip, int(PORT_1)
    )
    assert res3['op'] == 'REPLY'
    await ensure_pool_is_in_sync(nodes_num=5)

    # set rule for schema adding with off ledger parameters
    req = await ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
                                               json.dumps({
                                                    'constraint_id': 'OR',
                                                    'auth_constraints': [
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '0',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'off_ledger_signature': False,
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
    res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res4)
    assert res4['op'] == 'REPLY'

    # set rule for revoc reg def adding
    req = await ledger.build_auth_rule_request(trustee_did, '113', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': '2',
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res5)
    assert res5['op'] == 'REPLY'

    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=25)
    await ensure_pool_is_in_sync(nodes_num=5)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)


@pytest.mark.asyncio
async def test_misc_get_auth_rule():
    pool_handle, _ = await pool_helper(path_to_genesis='/home/indy/indy-test-automation/system/buildernet_genesis')
    req = await ledger.build_get_auth_rule_request(None, None, None, None, None, None)
    res = json.loads(await ledger.submit_request(pool_handle, req))
    print('\n', res)


@pytest.mark.asyncio
# INDY-2215
async def test_misc_catchup_special_case(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
):
    docker_client = docker.from_env()
    trustee_did, _ = get_default_trustee

    primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
    assert docker_client.containers.list(
        filters={'name': 'node7'}
    )[0].exec_run(
        ['systemctl', 'stop', 'indy-node'], user='root'
    ).exit_code == 0
    # primary2 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=25)

    docker_client.networks.list(names=[NETWORK_NAME])[0].disconnect('node7')
    assert docker_client.containers.list(
        filters={'name': 'node7'}
    )[0].exec_run(
        ['systemctl', 'start', 'indy-node'], user='root'
    ).exit_code == 0

    # wait a few minutes
    await asyncio.sleep(120)

    client.networks.list(names=[NETWORK_NAME])[0].connect('node7')
    # await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary2)

    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)


@pytest.mark.asyncio
# SN-7
async def test_misc_drop_states(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
        check_no_failures_fixture
):
    trustee_did, _ = get_default_trustee

    # set auth rule for schema
    req = await ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
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
                                                           'role': '2',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {}
                                                       },
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '101',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {}
                                                       }
                                                   ]
                                               }))
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res1)
    assert res1['op'] == 'REPLY'

    # write schema
    schema_id, schema_json = await anoncreds.issuer_create_schema(
        trustee_did, random_string(5), '1.0', json.dumps(['name', 'age'])
    )
    req = await ledger.build_schema_request(trustee_did, schema_json)
    res2 = json.loads(
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    )
    print(res2)
    assert res2['op'] == 'REPLY'

    # stop Node7 -> drop all states -> start Node7
    node7 = NodeHost(7)
    node7.stop_service()
    time.sleep(3)
    for _ledger in ['pool', 'domain', 'config']:
        print(node7.run('rm -rf /var/lib/indy/sandbox/data/Node7/{}_state'.format(_ledger)))
    time.sleep(3)
    node7.start_service()

    # check that pool is ok
    await ensure_pool_is_in_sync()
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    # write some txns
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=10)

    # check again that pool is ok
    await ensure_pool_is_in_sync()
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)


@pytest.mark.asyncio
# INDY-2103
async def test_misc_error_message(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee

    trustee_did_2, trustee_vk_2 = await create_and_store_did(wallet_handler, json.dumps({}))
    trustee_did_3, trustee_vk_3 = await create_and_store_did(wallet_handler, json.dumps({}))
    some_did, some_vk = await create_and_store_did(wallet_handler, json.dumps({}))
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_2, trustee_vk_2, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_3, trustee_vk_3, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, some_did, some_vk, None, None)
    req = await ledger.build_nym_request(trustee_did, '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA',  None, None, None)

    req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_2, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_3, req)
    req = await ledger.multi_sign_request(wallet_handler, some_did, req)  # sign with extra did

    req = json.loads(req)
    req['signatures'][some_did] = req['signatures'][some_did][::-1]  # distort signature
    res = json.loads(await ledger.submit_request(pool_handler, json.dumps(req)))
    print(res)
    assert res['op'] == 'REQNACK'
    assert res['reason'].__contains__(
        'insufficient number of valid signatures, 4 is required but 3 valid and 1 invalid have been provided. '
        'The following signatures are invalid: did={}, signature={}'.format(some_did, req['signatures'][some_did])
    )  # new error message check


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
# ST-623
async def test_misc_order_during_rolling_upgrade(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
):
    trustee_did, _ = get_default_trustee
    dests = [
        'Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv', '8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb',
        'DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya', '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA',
    ]
    docker_4_schedule = json.dumps(
        dict(
            {dest: datetime.strftime(datetime.now(tz=timezone.utc) + timedelta(minutes=1+i*5), '%Y-%m-%dT%H:%M:%S%z')
             for dest, i in zip(dests, range(len(dests)))}
        )
    )

    # schedule pool upgrade
    req = await ledger.build_pool_upgrade_request(
        trustee_did, 'upgrade', '1.10.0.dev1083', 'start', hashlib.sha256().hexdigest(), 5, docker_4_schedule, None,
        True, False, 'indy-node'
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res)
    assert res['op'] == 'REPLY'

    # load pool during upgrade
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=1000)

    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
# staging net issue (INDY-2233)
async def test_misc_rotate_bls_and_get_txn(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
):
    docker_client = docker.from_env()
    trustee_did, _ = get_default_trustee
    steward_did, steward_vk = await create_and_store_did(
        wallet_handler, seed='000000000000000000000000Steward4'
    )
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=3)

    for i in range(25):
        # rotate bls keys for Node4
        res1 = docker_client.containers.list(
            filters={'name': 'node4'}
        )[0].exec_run(
            ['init_bls_keys', '--name', 'Node4'], user='indy'
        )
        bls_key, bls_key_pop = res1.output.decode().splitlines()
        bls_key, bls_key_pop = bls_key.split()[-1], bls_key_pop.split()[-1]
        data = json.dumps(
            {
                'alias': 'Node4',
                'blskey': bls_key,
                'blskey_pop': bls_key_pop
            }
        )
        req = await ledger.build_node_request(steward_did, '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA', data)
        res2 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req)
        )
        assert res2['op'] == 'REPLY'

        # write txn
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did)

        # get txn
        req = await ledger.build_get_txn_request(None, 'DOMAIN', 10)
        res3 = json.loads(await ledger.submit_request(pool_handler, req))
        assert res3['result']['seqNo'] is not None


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
async def test_misc_multiple_vc(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
):
    trustee_did, _ = get_default_trustee

    for i in range(10):
        primary, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p = NodeHost(primary)
        p.stop_service()
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        p.start_service()

    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=200, timeout=300)
    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
# INDY-2224
async def test_misc_vc(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
):
    client = docker.from_env()
    trustee_did, _ = get_default_trustee

    primary, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
    p = NodeHost(primary)

    p.stop_service()
    await asyncio.sleep(60)
    p.start_service()

    client.networks.list(names=[NETWORK_NAME])[0].disconnect('node4')
    await asyncio.sleep(120)
    client.networks.list(names=[NETWORK_NAME])[0].connect('node4')

    await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
    await ensure_pool_is_in_sync(nodes_num=nodes_num)


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
# INDY-2235
async def test_misc_restore_from_audit(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
):
    client = docker.from_env()
    test_nodes = [NodeHost(i) for i in range(1, nodes_num + 1)]
    trustee_did, _ = get_default_trustee

    primary1, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
    client.networks.list(names=[NETWORK_NAME])[0].disconnect('node1')
    primary2 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=25)

    for node in test_nodes[1:]:
        node.restart_service()
    client.networks.list(names=[NETWORK_NAME])[0].connect('node1')

    p2 = NodeHost(primary2)
    p2.stop_service()
    await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary2)
    p2.start_service()

    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)


@pytest.mark.parametrize(
    'node_txns_count, loops_count, concurrency', [
        (15, 3, False),
        (10, 5, False),
        (5, 7, False),
        (150, 3, True),
        (100, 5, True),
        (50, 7, True)
    ]
)
@pytest.mark.nodes_num(5)
@pytest.mark.asyncio
# INDY-2262
async def test_misc_node_and_vc_interleaved(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num,
        node_txns_count, loops_count, concurrency
):
    trustee_did, _ = get_default_trustee
    pool_info = get_pool_info('1')

    for i in range(loops_count):
        # find primary
        primary, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        # demote it to force VC
        await eventually(
            demote_node, pool_handler, wallet_handler, trustee_did, 'Node{}'.format(primary),
            pool_info['Node{}'.format(primary)], timeout=60
        )
        await pool.refresh_pool_ledger(pool_handler)
        # check VC status
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
        # send extra node txns
        if concurrency:  # send all txns at once concurrently
            tasks = []
            for _ in range(node_txns_count):
                task = send_nodes(
                    pool_handler, wallet_handler, trustee_did, count=1, alias='INACTIVE_NODE'
                )
                tasks.append(task)
            await asyncio.gather(*tasks, return_exceptions=True)
        else:  # send all txns one by one
            await eventually(
                send_nodes, pool_handler, wallet_handler, trustee_did, count=node_txns_count, alias='INACTIVE_NODE'
            )
        # promote ex-primary back
        await eventually(promote_node, pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)

    await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=10)
    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
async def test_misc_async(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee

    t0 = time.perf_counter()
    for i in range(100):
        await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
    t1 = time.perf_counter()
    print('\n{}'.format(t1 - t0))

    t2 = time.perf_counter()
    tasks = []
    for i in range(100):
        task = send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
        tasks.append(task)
    await asyncio.gather(*tasks)
    t3 = time.perf_counter()
    print('\n{}'.format(t3 - t2))


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
# INDY-2298
async def test_misc_do_not_restore_primaries(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
):
    # initial version for this case is 1.11.0 stable, final version is the latest master, use both repos in setup
    trustee_did, _ = get_default_trustee
    versions = {
        'sovrin_ver': '1.1.167',
        'node_ver': '1.12.0~dev1138',
        'plenum_ver': '1.12.0~dev962',
        'plugin_ver': '1.0.5~dev118'
    }

    primary1, alias, node_did = await get_primary(pool_handler, wallet_handler, trustee_did)
    await demote_node(pool_handler, wallet_handler, trustee_did, alias, node_did)
    primary2 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
    await promote_node(pool_handler, wallet_handler, trustee_did, alias, node_did)
    await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary2)

    containers = [client.containers.get('node{}'.format(i)) for i in range(1, 5)]

    upgrade_nodes_manually(containers[:-1], **versions)

    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=10)

    upgrade_nodes_manually([containers[-1]], **versions)

    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=10)
    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
# IS-1381
async def test_misc_multiple_restrictions(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    issuer_did, _ = get_default_trustee
    prover_did, prover_vk = await create_and_store_did(wallet_handler)

    schema_id, res1 = await send_schema(
        pool_handler, wallet_handler, issuer_did, 'Schema 1', '1.0', json.dumps(['first_name', 'last_name', 'age'])
    )
    assert res1['op'] == 'REPLY'

    await asyncio.sleep(1)
    res = await get_schema(pool_handler, wallet_handler, issuer_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, cred_def_json, res2 = await send_cred_def(
        pool_handler, wallet_handler, issuer_did, schema_json, 'Tag 1', None, json.dumps({'support_revocation': False})
    )
    assert res2['op'] == 'REPLY'

    master_secret_id = await anoncreds.prover_create_master_secret(wallet_handler, 'Master secret 1')
    cred_offer_json = await anoncreds.issuer_create_credential_offer(wallet_handler, cred_def_id)
    cred_req_json, cred_req_metadata_json = await anoncreds.prover_create_credential_req(
        wallet_handler, prover_did, cred_offer_json, cred_def_json, master_secret_id
    )
    cred_json, cred_revoc_id, revoc_reg_delta_json = await anoncreds.issuer_create_credential(
        wallet_handler, cred_offer_json, cred_req_json, json.dumps(
            {
                "first_name":
                    {
                        "raw": "Pyotr",
                        # "encoded": "111"
                        "encoded": "1139480000000000000001716456278103335"
                    },
                "last_name":
                    {
                        "raw": "Pustota",
                        # "encoded": "222"
                        "encoded": "000000000000000000000000000000000000000000000000000000000000000000000000000000000"
                    },
                "age":
                    {
                        "raw": "99",
                        # "encoded": "333"
                        "encoded": "0000000000000000000000000000000000000001230000"
                        # "encoded": "100000000000000000000000000000000000000000000000000000009"
                    }
            }
        ), None, None
    )
    cred_id = await anoncreds.prover_store_credential(
        wallet_handler, None, cred_req_metadata_json, cred_json, cred_def_json, None
    )

    # proof request
    proof_request = json.dumps(
        {
            "nonce": "123432421212",
            # "nonce": hex(123456),
            # "nonce": random_string(10),
            "name": "proof_req_1",
            "version": "0.1",
            "requested_attributes":
                {
                    "attr1_referent":
                        {
                            "names": ["first_name", "last_name"],
                            "restrictions": []
                        }
                },
            "requested_predicates":
                {
                    "predicate1_referent":
                        {
                            "name": "age",
                            "p_type": ">=",
                            "p_value": 18,
                            "restrictions": []
                        }
                }
        }
    )

    credentials = await anoncreds.prover_get_credentials_for_proof_req(wallet_handler, proof_request)
    print('\nCREDENTIALS:')
    pprint.pprint(json.loads(credentials))

    search_handle = await anoncreds.prover_search_credentials_for_proof_req(wallet_handler, proof_request, None)

    creds_for_attr1 = await anoncreds.prover_fetch_credentials_for_proof_req(
        search_handle, 'attr1_referent', 10
    )
    cred_for_attr1 = json.loads(creds_for_attr1)[0]['cred_info']

    creds_for_predicate1 = await anoncreds.prover_fetch_credentials_for_proof_req(
        search_handle, 'predicate1_referent', 10
    )
    cred_for_predicate1 = json.loads(creds_for_predicate1)[0]['cred_info']

    await anoncreds.prover_close_credentials_search_for_proof_req(search_handle)

    # primary proof
    requested_credentials_json = json.dumps(
        {
            "self_attested_attributes": {},
            "requested_attributes":
                {
                    "attr1_referent":
                        {
                            "cred_id": cred_for_attr1['referent'],
                            "revealed": True
                        }
                },
            "requested_predicates":
                {
                    "predicate1_referent":
                        {
                            "cred_id": cred_for_predicate1['referent']
                        }
                }
        }
    )

    schemas_json = json.dumps(
        {schema_id: json.loads(schema_json)}
    )
    cred_defs_json = json.dumps(
        {cred_def_id: json.loads(cred_def_json)}
    )

    proof = await anoncreds.prover_create_proof(
        wallet_handler, proof_request, requested_credentials_json, master_secret_id, schemas_json, cred_defs_json, '{}'
    )
    print('\nREQUESTED PROOF:')
    pprint.pprint(json.loads(proof)['requested_proof'])

    assert 'Pyotr' ==\
           json.loads(proof)['requested_proof']['revealed_attr_groups']['attr1_referent']['values']['first_name']['raw']
    assert 'Pustota' ==\
           json.loads(proof)['requested_proof']['revealed_attr_groups']['attr1_referent']['values']['last_name']['raw']
    assert await anoncreds.verifier_verify_proof(proof_request, proof, schemas_json, cred_defs_json, '{}', '{}')


@pytest.mark.asyncio
# INDY-2216 / INDY-2303
async def test_misc_upgrades(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, check_no_failures_fixture
):
    trustee_did, _ = get_default_trustee
    version = '1.1.186'
    status = 'Active: active (running)'

    req = await ledger.build_pool_upgrade_request(
        trustee_did,
        random_string(10),
        version,
        'start',
        hashlib.sha256().hexdigest(),
        5,
        docker_7_schedule,
        None,
        False,
        True,
        'sovrin'
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    await asyncio.sleep(600)

    docker_7_hosts = [
        testinfra.get_host('docker://node' + str(i)) for i in range(1, 8)
    ]
    version_outputs = [host.run('dpkg -l | grep sovrin') for host in docker_7_hosts]
    status_outputs = [host.run('systemctl status indy-node') for host in docker_7_hosts]
    version_checks = [output.stdout.find(version.split('.')[-1]) for output in version_outputs]
    status_checks = [output.stdout.find(status) for output in status_outputs]
    assert all([check is not -1 for check in version_checks])
    assert all([check is not -1 for check in status_checks])


@pytest.mark.asyncio
# INDY-2306
async def test_misc_big_schema(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
):
    trustee_did, _ = get_default_trustee
    schema_id_local, res1 = await send_schema(
        pool_handler, wallet_handler, trustee_did, 'schema1', '1.0', json.dumps(
            [random_string(256) for i in range(125)]
        )
    )
    print(res1)
    assert res1['op'] == 'REPLY'

    res2 = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id_local)
    print(res2)

    schema_id_ledger, schema_json = await ledger.parse_get_schema_response(json.dumps(res2))
    assert schema_id_local == schema_id_ledger
    assert res2['result']['seqNo'] == json.loads(schema_json)['seqNo']

    cred_def_id_local, _, res3 = await send_cred_def(
        pool_handler, wallet_handler, trustee_did, schema_json, random_string(256), None, json.dumps(
            {'support_revocation': True}
        )
    )
    print(res3)
    assert res3['op'] == 'REPLY'

    res4 = await get_cred_def(pool_handler, wallet_handler, trustee_did, cred_def_id_local)
    print(res4)

    cred_def_id_ledger, cred_def_json = await ledger.parse_get_cred_def_response(json.dumps(res4))
    assert cred_def_id_local == cred_def_id_ledger


@pytest.mark.parametrize('state_proof_check', [False, True])
@pytest.mark.asyncio
# INDY-2302 / INDY-2316
async def test_misc_new_taa(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture,
    state_proof_check
):
    trustee_did, _ = get_default_trustee
    timestamp1 = int(time.time()) - 24*60*60

    # write and read a few nyms without TAA
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)

    # send nym with TAA before AML and TAA
    req01 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req01 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req01, 'taa text', '0.1', None, 'non_existent_aml_key', int(time.time())
    )
    res01 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req01))
    print(res01)
    assert res01['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res01)))
    assert res01['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    aml_key = 'aml_key'
    req = await ledger.build_acceptance_mechanisms_request(
        trustee_did, json.dumps({aml_key: random_string(128)}), random_string(256), random_string(1024)
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send nym with TAA after AML but before TAA - existing AML_KEY
    req02 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req02 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req02, 'another taa text', '0.2', None, aml_key, int(time.time())
    )
    res02 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req02))
    print(res02)
    assert res02['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res02)))
    assert res02['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send nym with TAA after AML but before TAA - non-existent AML_KEY
    req03 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req03 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req03, 'one more taa text', '0.3', None, 'non_existent_aml_key', int(time.time())
    )
    res03 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req03))
    print(res03)
    assert res03['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res03)))
    assert res03['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    req1 = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 1 text', '1.0', ratification_ts=int(time.time())
    )
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req1))
    print(res1)
    assert res1['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res1)))
    assert res1['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # cannot send nym without appended TAA with TAA enabled on ledger
    res_negative = await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
    assert res_negative['op'] == 'REJECT'

    req2 = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 2 text', '2.0', ratification_ts=int(time.time())
    )
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req2))
    print(res2)
    assert res2['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res2)))
    assert res2['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    req99 = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 3 text', '3.0', ratification_ts=int(time.time())
    )
    res99 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req99))
    print(res99)
    assert res99['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res99)))
    assert res99['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    if state_proof_check:
        test_nodes = [NodeHost(i) for i in range(1, nodes_num + 1)]
        for node in test_nodes[:-1]:
            node.stop_service()
        await asyncio.sleep(5)

    req = await ledger.build_get_txn_author_agreement_request(None, json.dumps({'version': '1.0'}))
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    assert res['result']['seqNo'] is not None
    assert res['result']['data']['digest'] is not None
    assert res['result']['data']['ratification_ts'] is not None
    assert 'retirement_ts' not in res['result']['data']
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['seqNo'] == parsed['seqNo']

    req = await ledger.build_get_txn_author_agreement_request(None, json.dumps({'version': '2.0'}))
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    assert res['result']['seqNo'] is not None
    assert res['result']['data']['digest'] is not None
    assert res['result']['data']['ratification_ts'] is not None
    assert 'retirement_ts' not in res['result']['data']
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['seqNo'] == parsed['seqNo']

    if state_proof_check:
        for node in test_nodes[:-1]:
            node.start_service()
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)

    req3 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req3 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req3, 'taa 1 text', '1.0', None, aml_key, int(time.time())
    )
    res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req3))
    print(res3)
    assert res3['op'] == 'REPLY'

    req4 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req4 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req4, 'taa 2 text', '2.0', None, aml_key, int(time.time())
    )
    res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req4))
    print(res4)
    assert res4['op'] == 'REPLY'

    # retire TAA2 without text
    req11 = await ledger.build_txn_author_agreement_request(trustee_did, None, '2.0', retirement_ts=timestamp1)
    res11 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req11))
    print(res11)
    assert res11['op'] == 'REPLY'

    req = await ledger.build_get_txn_author_agreement_request(None, json.dumps({'version': '2.0'}))
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    assert res['result']['seqNo'] is not None
    assert res['result']['data']['digest'] is not None
    assert res['result']['data']['ratification_ts'] is not None
    assert res['result']['data']['retirement_ts'] is not None
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['seqNo'] == parsed['seqNo']

    req5 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req5 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req5, 'taa 1 text', '1.0', None, aml_key, int(time.time())
    )
    res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req5))
    print(res5)
    assert res5['op'] == 'REPLY'

    req6 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req6 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req6, 'taa 2 text', '2.0', None, aml_key, int(time.time())
    )
    res6 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req6))
    print(res6)
    assert res6['op'] == 'REJECT'

    # retire TAA1 with text
    req22 = await ledger.build_txn_author_agreement_request(trustee_did, 'taa 1 text', '1.0', retirement_ts=timestamp1)
    res22 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req22))
    print(res22)
    assert res22['op'] == 'REPLY'

    req66 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req66 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req66, 'taa 1 text', '1.0', None, aml_key, int(time.time())
    )
    res66 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req66))
    print(res66)
    assert res66['op'] == 'REJECT'

    req = await ledger.build_get_txn_author_agreement_request(None, json.dumps({'version': '1.0'}))
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    assert res['result']['seqNo'] is not None
    assert res['result']['data']['digest'] is not None
    assert res['result']['data']['ratification_ts'] is not None
    assert res['result']['data']['retirement_ts'] is not None
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['seqNo'] == parsed['seqNo']

    req55 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req55 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req55, 'taa 3 text', '3.0', None, aml_key, int(time.time())
    )
    res55 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req55))
    print(res55)
    assert res55['op'] == 'REPLY'

    # send TRANSACTION_AUTHOR_AGREEMENT_DISABLE
    req = await ledger.build_disable_all_txn_author_agreements_request(trustee_did)
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

    if state_proof_check:
        test_nodes = [NodeHost(i) for i in range(1, nodes_num + 1)]
        for node in test_nodes[:-1]:
            node.stop_service()
        await asyncio.sleep(5)

    for i in [{'version': '1.0'}, {'version': '2.0'}, {'version': '3.0'}]:
        req = await ledger.build_get_txn_author_agreement_request(None, json.dumps(i))
        res = json.loads(await ledger.submit_request(pool_handler, req))
        assert res['op'] == 'REPLY'
        assert res['result']['seqNo'] is not None
        assert res['result']['data']['digest'] is not None
        assert res['result']['data']['ratification_ts'] is not None
        assert res['result']['data']['retirement_ts'] is not None
        parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
        assert res['result']['seqNo'] == parsed['seqNo']

    if state_proof_check:
        for node in test_nodes[:-1]:
            node.start_service()
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)

    # check that sending forced write transactions still work
    custom_schedule = json.dumps(
        dict(
            {
                dest: datetime.strftime(
                    datetime.now(tz=timezone.utc) + timedelta(days=1), '%Y-%m-%dT%H:%M:%S%z'
                ) for dest, i in zip(docker_7_destinations, range(len(docker_7_destinations)))
            }
        )
    )

    req = await ledger.build_pool_upgrade_request(
        trustee_did,
        random_string(10),
        '9.9.999',
        'start',
        hashlib.sha256().hexdigest(),
        5,
        custom_schedule,
        None,
        False,
        True,
        'sovrin'
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'

    req7 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req7 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req7, 'taa 1 text', '1.0', None, aml_key, int(time.time())
    )
    res7 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req7))
    print(res7)
    assert res7['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res7)))
    assert res7['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    req8 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req8 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req8, 'taa 2 text', '2.0', None, aml_key, int(time.time())
    )
    res8 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req8))
    print(res8)
    assert res8['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res8)))
    assert res8['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)


@pytest.mark.asyncio
# INDY-2302 / INDY-2316
# keep containers from previous test -> downgrade libindy and python3-indy (1.12.0~1356) -> run this test
async def test_misc_new_taa_reading_by_old_client(pool_handler, nodes_num):

    test_nodes = [NodeHost(i) for i in range(1, nodes_num + 1)]
    for node in test_nodes[:-1]:
        node.stop_service()

    await asyncio.sleep(5)

    for i in [{'version': '1.0'}, {'version': '2.0'}, {'version': '3.0'}]:
        req = await ledger.build_get_txn_author_agreement_request(None, json.dumps(i))
        res = json.loads(await ledger.submit_request(pool_handler, req))
        print(res)
        assert res['op'] == 'REPLY'
        assert res['result']['seqNo'] is not None
        assert res['result']['data']['digest'] is not None
        assert res['result']['data']['ratification_ts'] is not None
        assert res['result']['data']['retirement_ts'] is not None

    for node in test_nodes[:-1]:
        node.start_service()


@pytest.mark.asyncio
# INDY-2302 / INDY-2313 / INDY-2316
# ratification_ts - activation timestamp, mandatory for creation, optional for update
# retirement_ts - deactivation timestamp, forbidden for creation, optional for update
# taa text - mandatory for creation, optional for update
async def test_misc_new_taa_full_flow(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
):
    trustee_did, _ = get_default_trustee
    timestamp = int(time.time()) - 24*60*60

    # create AML - pass
    aml_key = 'aml_key'
    req = await ledger.build_acceptance_mechanisms_request(
        trustee_did, json.dumps({aml_key: random_string(128)}), random_string(256), random_string(1024)
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # create TAA 1 without ratification_ts - fail
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 1 text', '1.0'
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REJECT'

    # create TAA 1 with ratification_ts - pass
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, 'another taa 1 text', '1.1', ratification_ts=int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send NYM without TAA appended - fail
    res = await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
    assert res['op'] == 'REJECT'

    # send NYM with TAA 1 appended - pass
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'another taa 1 text', '1.1', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # update the latest TAA 1 to retire it - fail
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, None, '1.1', retirement_ts=timestamp
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REJECT'

    # send NYM with TAA 1 appended - pass
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'another taa 1 text', '1.1', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # create TAA 2 with ratification_ts - pass
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 2 text', '2.0', ratification_ts=int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send NYM with TAA 2 appended - pass
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'taa 2 text', '2.0', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # update NOT the latest TAA 1 to retire it - pass
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, None, '1.1', retirement_ts=timestamp
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send NYM with TAA 1 appended - fail
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'another taa 1 text', '1.1', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REJECT'

    # update TAA 1 to remove retirement - pass
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, None, '1.1', retirement_ts=None
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send NYM with TAA 1 appended - pass
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'another taa 1 text', '1.1', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send TRANSACTION_AUTHOR_AGREEMENT_DISABLE to retire all TAA
    req = await ledger.build_disable_all_txn_author_agreements_request(trustee_did)
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send NYM without TAA appended - pass
    res = await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
    assert res['op'] == 'REPLY'

    # update TAA 2 to remove retirement - fail
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, None, '2.0', retirement_ts=None
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REJECT'

    # create TAA 3 with ratification_ts - pass
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 3 text', '3.0', ratification_ts=int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send NYM with TAA 2 appended - fail
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'taa 2 text', '2.0', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REJECT'

    # send NYM with TAA 3 appended - pass
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'taa 3 text', '3.0', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # update the latest TAA 3 to retire it - fail
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, None, '3.0', retirement_ts=timestamp
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REJECT'

    # create TAA 4 with ratification_ts - pass
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, random_string(256), random_string(256), ratification_ts=int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # update NOT the latest TAA 3 with explicit text to retire it - pass
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 3 text', '3.0', retirement_ts=timestamp
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send NYM with TAA 3 appended - fail
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'taa 3 text', '3.0', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REJECT'

    # update TAA 3 with explicit text to remove retirement - pass
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 3 text', '3.0', retirement_ts=None
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send NYM with TAA 3 appended - pass
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'taa 3 text', '3.0', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)


@pytest.mark.asyncio
async def test_misc_taa_versions(
    docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
):
    trustee_did, _ = get_default_trustee
    timestamp = int(time.time()) - 24*60*60

    # create AML
    aml_key = 'aml_key'
    req = await ledger.build_acceptance_mechanisms_request(
        trustee_did, json.dumps({aml_key: random_string(128)}), random_string(256), random_string(1024)
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # create TAA 1 with version 1
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 1 text', '1', ratification_ts=int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # create TAA 2 with version 1.0
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, 'taa 2 text', '1.0', ratification_ts=int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # retire TAA 1
    req = await ledger.build_txn_author_agreement_request(
        trustee_did, None, '1', retirement_ts=timestamp
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']

    # send NYM with TAA 2 appended
    req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req = await ledger.append_txn_author_agreement_acceptance_to_request(
        req, 'taa 2 text', '1.0', None, aml_key, int(time.time())
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res)
    assert res['op'] == 'REPLY'
    parsed = json.loads(await ledger.get_response_metadata(json.dumps(res)))
    assert res['result']['txnMetadata']['seqNo'] == parsed['seqNo']


def test_misc_aws_demotion_promotion():
    interval = 180
    nodes_num = 3
    loop = asyncio.get_event_loop()
    loop.run_until_complete(indy_vdr.set_protocol_version(2))
    pool_cfg = json.dumps({"genesis_txn": "../aws_genesis_test"})
    pool_name = "pool_{}".format(random_string(24))
    loop.run_until_complete(pool.create_pool_ledger_config(pool_name, pool_cfg))
    pool_handle = loop.run_until_complete(pool.open_pool_ledger(pool_name, None))
    wallet_cfg = json.dumps({"id": "wallet_{}".format(random_string(24))})
    wallet_creds = json.dumps({"key": ""})
    loop.run_until_complete(wallet.create_wallet(wallet_cfg, wallet_creds))
    wallet_handle = loop.run_until_complete(wallet.open_wallet(wallet_cfg, wallet_creds))
    trustee_did, _ = loop.run_until_complete(
        create_and_store_did(wallet_handle, seed='000000000000000000000000Trustee1')
    )

    # read genesis to get aliases and dests
    with open('../aws_genesis_test', 'r') as f:
        data = f.read()
        jsons = [json.loads(x) for x in data.split('\n')]
        aliases = [_json['txn']['data']['data']['alias'] for _json in jsons]
        dests = [_json['txn']['data']['dest'] for _json in jsons]
    # put all into list of dicts
    pool_data = [
        {'node_alias': node_alias,
         'node_dest': node_dest}
        for node_alias, node_dest in zip(aliases, dests)
    ]

    async def _demote_promote_periodic():
        while True:
            # pick random node(s) from pool to demote/promote it
            req_data_list = random.sample(pool_data[:-1], nodes_num)  # keep 25th node always in pool

            for req_data in req_data_list:
                try:
                    await demote_node(
                        pool_handle, wallet_handle, trustee_did, req_data['node_alias'], req_data['node_dest']
                    )
                    # stop demoted node
                    host = testinfra.get_host('ssh://persistent_node' + req_data['node_alias'][4:])
                    host.run('sudo systemctl stop indy-node')
                except PoolLedgerTimeout:
                    await asyncio.sleep(interval)
                    continue

            # wait for an interval
            await asyncio.sleep(interval)

            for req_data in req_data_list:
                _data = {
                    'alias': req_data['node_alias'],
                    'services': ['VALIDATOR']
                }
                try:
                    req = await ledger.build_node_request(trustee_did, req_data['node_dest'], json.dumps(_data))
                    await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req)
                    # start promoted node
                    host = testinfra.get_host('ssh://persistent_node' + req_data['node_alias'][4:])
                    host.run('sudo systemctl start indy-node')
                except PoolLedgerTimeout:
                    await asyncio.sleep(interval)

                    req = await ledger.build_node_request(trustee_did, req_data['node_dest'], json.dumps(_data))
                    await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req)
                    # start promoted node
                    host = testinfra.get_host('ssh://persistent_node' + req_data['node_alias'][4:])
                    host.run('sudo systemctl start indy-node')

    loop = asyncio.get_event_loop()
    task = loop.create_task(_demote_promote_periodic())
    loop.call_later(interval * 100, task.cancel)

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass


@pytest.mark.parametrize('demote_count', [1, 100])
@pytest.mark.parametrize('promote_count', [1, 5])
@pytest.mark.asyncio
async def test_misc_redundant_demotions_promotions(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, check_no_failures_fixture,
        nodes_num, demote_count, promote_count
):
    trustee_did, _ = get_default_trustee
    pool_info = get_pool_info('1')
    node_list = ['Node{}'.format(x) for x in range(1, nodes_num + 1)]

    # find primary
    primary, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
    # select random node
    node_to_demote = choice(node_list)
    # demote it
    demote_tasks = []
    for i in range(demote_count):
        task = demote_node(pool_handler, wallet_handler, trustee_did, node_to_demote, pool_info[node_to_demote])
        demote_tasks.append(task)
    await asyncio.gather(*demote_tasks, return_exceptions=True)
    await pool.refresh_pool_ledger(pool_handler)
    # make sure VC is done
    new_primary = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
    new_primary_name = 'Node{}'.format(new_primary)
    # demote new primary
    demote_tasks = []
    for i in range(demote_count):
        task = demote_node(
            pool_handler, wallet_handler, trustee_did, new_primary_name, pool_info[new_primary_name]
        )
        demote_tasks.append(task)
    await asyncio.gather(*demote_tasks, return_exceptions=True)
    await pool.refresh_pool_ledger(pool_handler)
    # make sure VC is done
    super_new_primary = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, new_primary)
    # write txn
    req = await ledger.build_attrib_request(trustee_did, trustee_did, None, None, random_string(256))
    await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
    # promote both nodes back simultaneously
    promote_tasks = []
    for i in range(promote_count):
        task1 = promote_node(pool_handler, wallet_handler, trustee_did, node_to_demote, pool_info[node_to_demote])
        promote_tasks.append(task1)
        task2 = promote_node(
            pool_handler, wallet_handler, trustee_did, new_primary_name, pool_info[new_primary_name]
        )
        promote_tasks.append(task2)
    await asyncio.gather(*promote_tasks, return_exceptions=True)
    await pool.refresh_pool_ledger(pool_handler)
    # make sure VC is done
    await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, super_new_primary)

    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=10)
    await ensure_pool_is_okay(pool_handler, wallet_handler, trustee_did)


@pytest.mark.parametrize('iterations', [1, 5])
@pytest.mark.parametrize('nyms_count', [10, 20])
@pytest.mark.asyncio
async def test_misc_cyclic_demotions_promotions(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, check_no_failures_fixture,
        nodes_num, iterations, nyms_count
):
    trustee_did, _ = get_default_trustee
    pool_info = get_pool_info('1')
    node_list = ['Node{}'.format(x) for x in range(1, nodes_num + 1)]

    for _ in range(iterations):
        # find primary
        primary, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        # select random node
        node_to_demote = choice(node_list)
        # demote it
        await demote_node(pool_handler, wallet_handler, trustee_did, node_to_demote, pool_info[node_to_demote])
        await pool.refresh_pool_ledger(pool_handler)
        # make sure VC is done
        new_primary = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
        # make sure pool works
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=nyms_count)
        # write txn
        req = await ledger.build_attrib_request(trustee_did, trustee_did, None, None, random_string(256))
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        # promote node back
        await promote_node(pool_handler, wallet_handler, trustee_did, node_to_demote, pool_info[node_to_demote])
        await pool.refresh_pool_ledger(pool_handler)
        # make sure VC is done
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, new_primary)
        # make sure pool works
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=nyms_count)

    await ensure_pool_is_okay(pool_handler, wallet_handler, trustee_did)


@pytest.mark.asyncio
async def test_misc_check_new_helpers(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee
    for _ in range(10):
        t = time.perf_counter()
        req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
        await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        print('\n{}'.format(time.perf_counter() - t))

    await ensure_pool_is_okay(pool_handler, wallet_handler, trustee_did)


@pytest.mark.nodes_num(10)
@pytest.mark.asyncio
async def test_misc_demotions(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
):
    trustee_did, _ = get_default_trustee
    pool_info = get_pool_info('1')
    node_list = ['Node{}'.format(x) for x in range(1, nodes_num + 1)]

    for node in node_list[:-4]:
        # find primary
        primary, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        # demote node
        await demote_node(pool_handler, wallet_handler, trustee_did, node, pool_info[node])
        await pool.refresh_pool_ledger(pool_handler)
        # make sure VC is done
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
        # make sure pool works
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)


@pytest.mark.nodes_num(4)
@pytest.mark.asyncio
async def test_misc_demotions(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee
):
    trustee_did, _ = get_default_trustee
    req = await ledger.build_get_txn_request(None, '3', 1)
    res = json.loads(await ledger.submit_request(pool_handler, req))
    print(res)
    assert res['result']['seqNo'] is not None


@pytest.mark.nodes_num(4)
@pytest.mark.parametrize(
    'xhash, raw, enc',
    [
        (hashlib.sha256().hexdigest(), None, None),
        (None, json.dumps({'key': random_string(256)}), None),
        (None, None, random_string(256))
    ]
)
@pytest.mark.asyncio
# IS-1515
async def test_misc_attrib_reading(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num, xhash, raw, enc
):
    trustee_did, _ = get_default_trustee
    random_did = random_did_and_json()[0]

    res_nym = await send_nym(pool_handler, wallet_handler, trustee_did, random_did)
    assert res_nym['op'] == 'REPLY'

    res_attr = await send_attrib(
        pool_handler, wallet_handler, trustee_did, random_did, xhash, raw, enc
    )
    print(res_attr)
    assert res_attr['op'] == 'REPLY'

    # stop all nodes except one
    hosts = [NodeHost(i) for i in range(1, nodes_num+1)]
    print([host.stop_service() for host in hosts[:-1]])

    req = await ledger.build_get_txn_request(None, 'DOMAIN', res_attr['result']['txnMetadata']['seqNo'])
    res = json.loads(await ledger.submit_request(pool_handler, req))
    print(res)
    assert res['result']['seqNo'] is not None
