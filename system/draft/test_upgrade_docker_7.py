from system.utils import *
from system.utils import create_and_store_did
import pytest
import hashlib
import time
import asyncio
from datetime import datetime, timedelta, timezone
import json
import testinfra
from system.docker_setup import client, pool_builder, pool_starter,\
    DOCKER_BUILD_CTX_PATH, DOCKER_IMAGE_NAME, NETWORK_NAME


# TODO dynamic install of old version to upgrade from
# TODO INDY-2132 and INDY-2125
@pytest.mark.asyncio
# previous -> latest
async def test_pool_upgrade_positive(
        docker_setup_and_teardown, pool_handler, wallet_handler, check_no_failures_fixture
):
    # ------------------EXTRA NODE SETUP--------------------------------------------------------------------------------
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

    new_ip = '10.0.0.9'
    PORT_1 = '9701'
    PORT_2 = '9702'
    new_alias = 'Node8'

    # initialize
    assert new_node.exec_run(
        ['init_indy_node', new_alias, new_ip, PORT_1, new_ip, PORT_2, '000000000000000000000000000node8'],
        user='indy'
    ).exit_code == 0

    # upgrade it to the target version of pool upgrade command
    plenum_ver = '1.12.3'
    plenum_pkg = 'indy-plenum'
    node_ver = '1.12.3~rc1'
    node_pkg = 'indy-node'
    sovrin_ver = '1.1.78'
    sovrin_pkg = 'sovrin'
    plugin_ver = '1.0.8~rc34'
    # repo_update = new_node.exec_run(
    #     [
    #         'sed',
    #         '-i',
    #             #TODO: find replacement for SOVRIN debs repo,
    #         '/etc/apt/sources.list'
    #     ]
    # )
    # print(repo_update.output)
    # assert repo_update.exit_code == 0
    # time.sleep(15)
    res = new_node.exec_run(
        ['apt', 'update'],
        user='root'
    )
    print(res.output)
    assert res.exit_code == 0
    res = new_node.exec_run(
        ['apt', 'install',
         '{}={}'.format(sovrin_pkg, sovrin_ver),
         '{}={}'.format(node_pkg, node_ver),
         '{}={}'.format(plenum_pkg, plenum_ver),
         '-y', '--allow-change-held-packages'],
        user='root'
    )
    print(res.output)
    assert res.exit_code == 0

    # ------------------------------------------------------------------------------------------------------------------

    dests = [
        'Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv', '8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb',
        'DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya', '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA',
        '4SWokCJWJc69Tn74VvLS6t2G2ucvXqM9FDMsWJjmsUxe', 'Cv1Ehj43DDM5ttNBmC6VPpEfwXWwfGktHwjDJsTV5Fz8',
        'BM8dTooz5uykCbYSAAFwKNkYfT4koomBHsSWHTDtkjhW'
    ]
    init_time = 5
    version = '1.1.78'
    status = 'Active: active (running)'
    name = 'upgrade'+'_'+version+'_'+datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
    action = 'start'
    _sha256 = hashlib.sha256().hexdigest()
    _timeout = 5
    docker_7_schedule = json.dumps(
        dict(
                {
                    dest: datetime.strftime(
                        datetime.now(tz=timezone.utc) + timedelta(minutes=init_time+i*5), '%Y-%m-%dT%H:%M:%S%z'
                    ) for dest, i in zip(dests, range(len(dests)))
                }
        )
    )
    reinstall = False
    force = False
    package = 'sovrin'
    random_did = random_did_and_json()[0]
    trustee_did, trustee_vk = await create_and_store_did(
        wallet_handler, seed='000000000000000000000000Trustee1'
    )

    # time.sleep(60)
    # # perform upgrade to the same version to write upgrade txn and wait for a while
    # # [from 1.1.35 installed to 1.1.35 | from 1.1.50 installed to 1.1.52]
    # req = await ledger.build_pool_upgrade_request(
    #     trustee_did, name, '1.1.50', action, _sha256, _timeout, docker_7_schedule, None, True, force, 'sovrin'
    # )
    # res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    # assert res['op'] == 'REPLY'
    # time.sleep(180)

    timestamp0 = int(time.time())

    steward_did, steward_vk = await create_and_store_did(wallet_handler)
    res = await send_nym(
        pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, 'Steward5', 'STEWARD'
    )
    assert res['op'] == 'REPLY'

    # write all txns before the upgrade
    nym_before_res = await send_nym(pool_handler, wallet_handler, trustee_did, random_did)
    attrib_before_res = await send_attrib(
        pool_handler, wallet_handler, trustee_did, random_did, None, json.dumps({'key': 'value'}), None
    )
    schema_id, schema_before_res = await send_schema(
        pool_handler, wallet_handler, trustee_did, random_string(10), '1.0', json.dumps(
            ["age", "sex", "height", "name"]
        )
    )
    time.sleep(5)
    temp = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(temp))

    cred_def_id, _, cred_def_before_res = await send_cred_def(
        pool_handler, wallet_handler, trustee_did, schema_json, random_string(5), 'CL', json.dumps(
            {'support_revocation': True}
        )
    )

    revoc_reg_def_id1, _, _, revoc_reg_def_before_res = await send_revoc_reg_def(
        pool_handler, wallet_handler, trustee_did, 'CL_ACCUM', random_string(5), cred_def_id, json.dumps(
            {'max_cred_num': 1, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}
        )
    )

    revoc_reg_def_id2, _, _, revoc_reg_entry_before_res = await send_revoc_reg_entry(
        pool_handler, wallet_handler, trustee_did, 'CL_ACCUM', random_string(5), cred_def_id, json.dumps(
            {'max_cred_num': 1, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}
        )
    )

    timestamp1 = int(time.time())

    # set auth rule for pool restart action
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

    # set rule for cred def adding with off ledger parameters
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

    await send_nodes(pool_handler, wallet_handler, trustee_did, 5, alias='ExtraNode')

    await send_upgrades(pool_handler, wallet_handler, trustee_did, 'indy-node', 5)
    await send_upgrades(pool_handler, wallet_handler, trustee_did, 'sovrin', 5)

    trustee_did2, trustee_vk2 = await create_and_store_did(
        wallet_handler, seed='000000000000000000000000Trustee2'
    )
    trustee_did3, trustee_vk3 = await create_and_store_did(
        wallet_handler, seed='000000000000000000000000Trustee3'
    )
    trustee_did4, trustee_vk4 = await create_and_store_did(
        wallet_handler, seed='000000000000000000000000Trustee4'
    )

    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did4, trustee_vk4, None, 'TRUSTEE')

    # ---

    # # POOL UPGRADE TO THE LATEST STABLE BEFORE APT INSTALL TO THE LATEST MASTER
    # time.sleep(60)
    # req = await ledger.build_pool_upgrade_request(
    #     trustee_did, name, '1.1.63', action, _sha256, _timeout, docker_7_schedule, None, reinstall, force, 'sovrin'
    # )
    # res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    # assert res['op'] == 'REPLY'
    # time.sleep(180)

    # schedule pool upgrade - for STABLE to STABLE upgrade
    req = await ledger.build_pool_upgrade_request(
        trustee_did, name, version, action, _sha256, _timeout, docker_7_schedule, None, reinstall, force, package
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res)
    assert res['op'] == 'REPLY'

    await asyncio.sleep(8*5*60)

    # # perform upgrade manually - for STABLE to MASTER upgrade
    # containers = [client.containers.get('node{}'.format(i)) for i in range(1, 8)]
    #
    # for container in containers:
    #
    #     assert container.exec_run(
    #         ['systemctl', 'stop', 'indy-node'],
    #         user='root'
    #     ).exit_code == 0
    #
    #     assert container.exec_run(
    #         ['systemctl', 'stop', 'indy-node-control'],
    #         user='root'
    #     ).exit_code == 0
    #
    # for container in containers:
    #
    #     repo_update = container.exec_run(
    #         [
    #             'sed',
    #             '-i',
    #             #TODO: find replacement for SOVRIN debs repo,
    #             '/etc/apt/sources.list'
    #         ]
    #     )
    #     print(repo_update.output)
    #     assert repo_update.exit_code == 0
    #     time.sleep(15)
    #     res = container.exec_run(
    #         ['apt', 'update'],
    #         user='root'
    #     )
    #     print(res.output)
    #     assert res.exit_code == 0
    #
    #     res = container.exec_run(
    #         ['apt', 'install',
    #          '{}={}'.format(sovrin_pkg, sovrin_ver),
    #          '{}={}'.format(node_pkg, node_ver),
    #          '{}={}'.format(plenum_pkg, plenum_ver),
    #          '-y', '--allow-change-held-packages'],
    #         user='root'
    #     )
    #     print(res.output)
    #     assert res.exit_code == 0
    #
    # for container in containers:
    #
    #     assert container.exec_run(
    #         ['systemctl', 'start', 'indy-node'],
    #         user='root'
    #     ).exit_code == 0
    #
    #     assert container.exec_run(
    #         ['systemctl', 'start', 'indy-node-control'],
    #         user='root'
    #     ).exit_code == 0

    # # cancel pool upgrade - optional
    # req = await ledger.build_pool_upgrade_request(
    #     trustee_did, name, version, 'cancel', _sha256, _timeout, docker_7_schedule, None, reinstall, force, package
    # )
    # res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    # print(res)
    # assert res['op'] == 'REPLY'

    # start new node
    assert new_node.exec_run(
        ['systemctl', 'start', 'indy-node'],
        user='root'
    ).exit_code == 0

    await asyncio.sleep(180)

    docker_7_hosts = [
        testinfra.get_host('docker://node' + str(i)) for i in range(1, 8)
    ]
    version_outputs = [host.run('dpkg -l | grep {}'.format(package)) for host in docker_7_hosts]
    print(version_outputs)
    status_outputs = [host.run('systemctl status indy-node') for host in docker_7_hosts]
    print(status_outputs)
    version_checks = [output.stdout.find(version.split('.')[-1]) for output in version_outputs]
    print(version_checks)
    status_checks = [output.stdout.find(status) for output in status_outputs]
    print(status_checks)

    # add new node
    # primary, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
    res = await send_node(
        pool_handler, wallet_handler, ['VALIDATOR'], steward_did, EXTRA_DESTS[3], new_alias,
        EXTRA_BLSKEYS[3], EXTRA_BLSKEY_POPS[3], new_ip, int(PORT_2), new_ip, int(PORT_1)
    )
    assert res['op'] == 'REPLY'
    # await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    # read all txns that were added before the upgrade
    get_nym_after_res = await get_nym(pool_handler, wallet_handler, trustee_did, random_did)
    get_attrib_after_res = await get_attrib(pool_handler, wallet_handler, trustee_did, random_did, None, 'key', None)
    get_schema_after_res = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
    get_cred_def_after_res = await get_cred_def(pool_handler, wallet_handler, trustee_did, cred_def_id)
    get_revoc_reg_def_after_res = await get_revoc_reg_def(
        pool_handler, wallet_handler, trustee_did, revoc_reg_def_id1
    )
    get_revoc_reg_after_res = await get_revoc_reg(
        pool_handler, wallet_handler, trustee_did, revoc_reg_def_id2, timestamp1
    )
    get_revoc_reg_delta_after_res = await get_revoc_reg_delta(
        pool_handler, wallet_handler, trustee_did, revoc_reg_def_id2, timestamp0, timestamp1
    )

    # set rule for schema adding with off ledger parameters
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
    print(res)
    assert res['op'] == 'REPLY'

    # set rule for revoc reg def adding without off ledger parameters
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

    # write and read NYM after the upgrade
    await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)

    # check that added node wrote all txns
    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    add_before_results = [
        nym_before_res, attrib_before_res, schema_before_res, cred_def_before_res, revoc_reg_def_before_res,
        revoc_reg_entry_before_res
    ]
    get_after_results = [
        get_nym_after_res, get_attrib_after_res, get_schema_after_res, get_cred_def_after_res,
        get_revoc_reg_def_after_res, get_revoc_reg_after_res, get_revoc_reg_delta_after_res
    ]

    # get all auth rules
    req = await ledger.build_get_auth_rule_request(None, None, None, None, None, None)
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'

    assert all([res['op'] == 'REPLY' for res in add_before_results])
    assert all([res['result']['seqNo'] is not None for res in get_after_results])
    assert all([check is not -1 for check in version_checks])
    assert all([check is not -1 for check in status_checks])

    # stop Node7 -> drop all states -> start Node7
    node7 = NodeHost(7)
    node7.stop_service()
    time.sleep(3)
    for _ledger in ['pool', 'domain', 'config']:
        print(node7.run('rm -rf /var/lib/indy/sandbox/data/Node7/{}_state'.format(_ledger)))
    time.sleep(3)
    node7.start_service()

    await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
