from system.utils import *
from system.docker_setup import create_new_node
import pytest
import hashlib
import time
import asyncio
import json


@pytest.mark.asyncio
# READ THIS BEFORE RUN THE TEST
# install 1.12.1~dev1163 / 1.12.1~dev978 (1.1.191 / 1.0.6~dev134)
# write TAA txns
# upgrade to X.X.XXX with force
# write TAA txns with new parameters
# add new node with the same version installed
# read TAA txns written and send ledger txns signed with TAA
# check ledgers and states
async def test_pool_upgrade_auth_rule(
        docker_setup_and_teardown, payment_init, pool_handler, wallet_handler, get_default_trustee,
        check_no_failures_fixture
):
    # SETUP ------------------------------------------------------------------------------------------------------------
    trustee_did, _ = get_default_trustee

    steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(
        pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, 'Steward5', 'STEWARD'
    )
    assert res['op'] == 'REPLY'

    aml_key = 'aml_key'
    req = await ledger.build_acceptance_mechanisms_request(
        trustee_did, json.dumps({aml_key: random_string(128)}), random_string(256), random_string(1024)
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'

    new_node_name = 'new_node'
    new_node_ip = '10.0.0.9'
    new_node_alias = 'Node8'
    new_node_seed = '000000000000000000000000000node8'
    sovrin_ver = '1.1.63'  # FIXME
    indy_node_ver = '1.12.0'  # FIXME
    indy_plenum_ver = '1.12.0'  # FIXME
    plugin_ver = '1.0.5'  # FIXME
    # ------------------------------------------------------------------------------------------------------------------

    # create new node and upgrade it to proper version
    new_node = create_new_node(
        new_node_name,
        new_node_ip,
        new_node_alias,
        new_node_seed,
        sovrin_ver,
        indy_node_ver,
        indy_plenum_ver,
        plugin_ver
    )

    req1 = await ledger.build_txn_author_agreement_request(trustee_did, 'taa 1 text', '1.0')
    res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req1))
    print(res1)
    assert res1['op'] == 'REPLY'

    req2 = await ledger.build_txn_author_agreement_request(trustee_did, '', '2.0')
    res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req2))
    print(res2)
    assert res2['op'] == 'REPLY'

    # upgrade pool
    await asyncio.sleep(60)
    req = await ledger.build_pool_upgrade_request(
        trustee_did,
        random_string(10),
        sovrin_ver,
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
    await asyncio.sleep(180)

    timestamp1 = int(time.time())

    req3 = await ledger.build_txn_author_agreement_request(trustee_did, '', '2.0', retired=timestamp1)
    res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req3))
    print(res3)
    assert res3['op'] == 'REPLY'

    # cannot create a transaction author agreement with a 'retired' field
    req4 = await ledger.build_txn_author_agreement_request(trustee_did, 'some text', '3.0', retired=timestamp1)
    res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req4))
    print(res4)
    assert res4['op'] == 'REJECT'

    req5 = await ledger.build_txn_author_agreement_request(trustee_did, 'taa 3 text', '3.0')
    res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req5))
    print(res5)
    assert res5['op'] == 'REPLY'

    # the latest transaction author agreement cannot be retired
    req6 = await ledger.build_txn_author_agreement_request(trustee_did, 'taa 3 text', '3.0', retired=timestamp1)
    res6 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req6))
    print(res6)
    assert res6['op'] == 'REJECT'

    # start new node
    assert new_node.exec_run(
        ['systemctl', 'start', 'indy-node'],
        user='root'
    ).exit_code == 0
    await asyncio.sleep(60)

    # add new node
    res = await send_node(
        pool_handler,
        wallet_handler,
        ['VALIDATOR'],
        steward_did,
        EXTRA_DESTS[3],
        new_node_alias,
        EXTRA_BLSKEYS[3],
        EXTRA_BLSKEY_POPS[3],
        new_node_ip,
        9702,
        new_node_ip,
        9701
    )
    assert res['op'] == 'REPLY'
    await pool.refresh_pool_ledger(pool_handler)
    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    # check config ledger writing
    req = await ledger.build_auth_rule_request(
        trustee_did, '118', 'ADD', 'action', '*', '*', json.dumps(
            {
                'constraint_id': 'ROLE',
                'role': '*',
                'sig_count': 1,
                'need_to_be_owner': False,
                'metadata': {}
            }
        )
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'

    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    # send GET_TAA for TAA1
    req = await ledger.build_get_txn_author_agreement_request(None, json.dumps({'version': '1.0'}))
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    assert res['result']['seqNo'] is not None

    # send GET_TAA for TAA2
    req = await ledger.build_get_txn_author_agreement_request(None, json.dumps({'version': '2.0'}))
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    assert res['result']['seqNo'] is not None

    # send GET_TAA for TAA3
    req = await ledger.build_get_txn_author_agreement_request(None, json.dumps({'version': '3.0'}))
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    assert res['result']['seqNo'] is not None

    # add TAA1 to nym - pass
    req7 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req7 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req7, 'taa 1 text', '1.0', None, aml_key, int(time.time())
    )
    res7 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req7))
    assert res7['op'] == 'REPLY'

    # add TAA2 to nym - fail (retired)
    req8 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req8 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req8, '', '2.0', None, aml_key, int(time.time())
    )
    res8 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req8))
    assert res8['op'] == 'REJECT'

    # add TAA3 to nym - pass
    req9 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req9 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req9, 'taa 3 text', '3.0', None, aml_key, int(time.time())
    )
    res9 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req9))
    assert res9['op'] == 'REPLY'

    req10 = await ledger.build_txn_author_agreement_request(trustee_did, '', '2.0', retired=None)
    res10 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req10))
    print(res10)
    assert res10['op'] == 'REPLY'

    # add TAA2 to nym - pass (not retired)
    req11 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req11 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req11, '', '2.0', None, aml_key, int(time.time())
    )
    res11 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req11))
    assert res11['op'] == 'REPLY'

    # add TAA2 to nym with old timestamp - fail (old timestamp)
    req12 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
    req12 = await ledger.append_txn_author_agreement_acceptance_to_request(
        req12, '', '2.0', None, aml_key, timestamp1
    )
    res12 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req12))
    assert res12['op'] == 'REJECT'
