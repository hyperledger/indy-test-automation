from system.utils import *
from system.docker_setup import create_new_node
import pytest
import hashlib
import time
import asyncio
import json


@pytest.mark.asyncio
# READ THIS BEFORE RUN THE TEST
# install 1.9.0 / 1.9.0 (1.1.50 / 1.0.0) with node_control_utils_1_1_52.py as node_control_utils.py
# upgrade to 1.1.52 with force (but without reinstall)
# write auth rule txns with and without off_ledger_signature
# upgrade to the latest rc/stable
# add new node with the same version installed
# write auth rule txns with and without off_ledger_signature
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

    new_node_name = 'new_node'
    new_node_ip = '10.0.0.9'
    new_node_alias = 'Node8'
    new_node_seed = '000000000000000000000000000node8'
    sovrin_ver = '1.1.63'
    indy_node_ver = '1.12.0'
    indy_plenum_ver = '1.12.0'
    plugin_ver = '1.0.5'
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

    # upgrade pool to 1.1.52 with force (but without reinstall)
    await asyncio.sleep(60)
    req = await ledger.build_pool_upgrade_request(
        trustee_did,
        random_string(10),
        '1.1.52',
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

    # set auth rule for pool restart action WITHOUT off ledger parameter
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

    # set rule for cred def adding WITH off ledger parameters
    req = await ledger.build_auth_rule_request(
        trustee_did, '102', 'ADD', '*', None, '*', json.dumps(
            {
                'constraint_id': 'OR',
                'auth_constraints':
                    [
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
            }
        )
    )

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

    # start new node
    assert new_node.exec_run(
        ['systemctl', 'start', 'indy-node'],
        user='root'
    ).exit_code == 0
    await asyncio.sleep(60)

    # add new node
    # primary, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
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
    # await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
    # check new node's catchup
    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    # set rule for revoc reg def adding WITHOUT off ledger parameter
    req = await ledger.build_auth_rule_request(
        trustee_did, '113', 'ADD', '*', None, '*', json.dumps(
            {
                'constraint_id': 'ROLE',
                'role': '2',
                'sig_count': 1,
                'need_to_be_owner': False,
                'metadata': {}
            }
        )
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'

    # set rule for schema adding WITH off ledger parameters
    req = await ledger.build_auth_rule_request(
        trustee_did, '101', 'ADD', '*', None, '*', json.dumps(
            {
                'constraint_id': 'OR',
                'auth_constraints':
                    [
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
            }
        )
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    assert res['op'] == 'REPLY'

    # write and read NYM after the upgrade
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)

    # get all auth rules
    req = await ledger.build_get_auth_rule_request(None, None, None, None, None, None)
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'

    # check new node's ordering
    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    # stop Node7 -> drop all states -> start Node7
    node7 = NodeHost(7)
    node7.stop_service()
    time.sleep(3)
    for _ledger in ['pool', 'domain', 'config', 'sovtoken']:
        print(node7.run('rm -rf /var/lib/indy/sandbox/data/Node7/{}_state'.format(_ledger)))
    time.sleep(3)
    node7.start_service()

    # check dropped node's recovery
    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
