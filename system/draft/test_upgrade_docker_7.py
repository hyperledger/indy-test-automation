from system.utils import *
from indy import did
import pytest
import hashlib
import time
import asyncio
from datetime import datetime, timedelta, timezone
import json
import testinfra


# TODO dynamic install of old version to upgrade from
# TODO INDY-2132 and INDY-2125
@pytest.mark.asyncio
async def test_pool_upgrade_positive(docker_setup_and_teardown):
    await pool.set_protocol_version(2)
    dests = [
        'Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv', '8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb',
        'DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya', '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA',
        '4SWokCJWJc69Tn74VvLS6t2G2ucvXqM9FDMsWJjmsUxe', 'Cv1Ehj43DDM5ttNBmC6VPpEfwXWwfGktHwjDJsTV5Fz8',
        'BM8dTooz5uykCbYSAAFwKNkYfT4koomBHsSWHTDtkjhW'
    ]
    init_time = 1
    version = '1.1.59'
    status = 'Active: active (running)'
    name = 'upgrade'+'_'+version+'_'+datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
    action = 'start'
    _sha256 = hashlib.sha256().hexdigest()
    _timeout = 5
    docker_7_schedule = json.dumps(dict(
        {dest:
            datetime.strftime(datetime.now(tz=timezone.utc) + timedelta(minutes=init_time+0*5), '%Y-%m-%dT%H:%M:%S%z')
         for dest, i in zip(dests, range(len(dests)))}
    ))
    reinstall = False
    force = True
    package = 'sovrin'
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    random_did = random_did_and_json()[0]
    another_random_did = random_did_and_json()[0]
    trustee_did, trustee_vk = await did.create_and_store_my_did(
        wallet_handle, json.dumps({'seed': '000000000000000000000000Trustee1'})
    )

    timestamp0 = int(time.time())

    # write all txns before the upgrade
    nym_before_res = await send_nym(pool_handle, wallet_handle, trustee_did, random_did)
    attrib_before_res = await send_attrib(
        pool_handle, wallet_handle, trustee_did, random_did, None, json.dumps({'key': 'value'}), None
    )
    schema_id, schema_before_res = await send_schema(
        pool_handle, wallet_handle, trustee_did, random_string(10), '1.0', json.dumps(["age", "sex", "height", "name"])
    )
    await asyncio.sleep(5)
    temp = await get_schema(pool_handle, wallet_handle, trustee_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(temp))

    cred_def_id, _, cred_def_before_res = await send_cred_def(
        pool_handle, wallet_handle, trustee_did, schema_json, random_string(5), 'CL',
        json.dumps({'support_revocation': True})
    )

    revoc_reg_def_id1, _, _, revoc_reg_def_before_res = await send_revoc_reg_def(
        pool_handle, wallet_handle, trustee_did, 'CL_ACCUM', random_string(5), cred_def_id,
        json.dumps({'max_cred_num': 1, 'issuance_type': 'ISSUANCE_BY_DEFAULT'})
    )

    revoc_reg_def_id2, _, _, revoc_reg_entry_before_res = await send_revoc_reg_entry(
        pool_handle, wallet_handle, trustee_did, 'CL_ACCUM', random_string(5), cred_def_id,
        json.dumps({'max_cred_num': 1, 'issuance_type': 'ISSUANCE_BY_DEFAULT'})
    )

    timestamp1 = int(time.time())

    # set auth rule for pool restart action
    req = await ledger.build_auth_rule_request(trustee_did, '118', 'ADD', 'action', '*', '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': '*',
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    print(res)
    assert res['op'] == 'REPLY'

    # schedule pool upgrade
    req = await ledger.build_pool_upgrade_request(
        trustee_did, name, version, action, _sha256, _timeout, docker_7_schedule, None, reinstall, force, package
    )
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    print(res)
    assert res['op'] == 'REPLY'

    # # cancel pool upgrade - optional
    # req = await ledger.build_pool_upgrade_request(
    #     trustee_did, name, version, 'cancel', _sha256, _timeout, docker_7_schedule, None, reinstall, force, package
    # )
    # res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    # print(res)
    # assert res['op'] == 'REPLY'

    await asyncio.sleep(5*60)

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

    # read all txns that were added before the upgrade
    get_nym_after_res = await get_nym(pool_handle, wallet_handle, trustee_did, random_did)
    get_attrib_after_res = await get_attrib(pool_handle, wallet_handle, trustee_did, random_did, None, 'key', None)
    get_schema_after_res = await get_schema(pool_handle, wallet_handle, trustee_did, schema_id)
    get_cred_def_after_res = await get_cred_def(pool_handle, wallet_handle, trustee_did, cred_def_id)
    get_revoc_reg_def_after_res = await get_revoc_reg_def(
        pool_handle, wallet_handle, trustee_did, revoc_reg_def_id1
    )
    get_revoc_reg_after_res = await get_revoc_reg(
        pool_handle, wallet_handle, trustee_did, revoc_reg_def_id2, timestamp1
    )
    get_revoc_reg_delta_after_res = await get_revoc_reg_delta(
        pool_handle, wallet_handle, trustee_did, revoc_reg_def_id2, timestamp0, timestamp1
    )

    # write and read NYM after the upgrade
    nym_res = await send_nym(pool_handle, wallet_handle, trustee_did, another_random_did)
    await asyncio.sleep(1)
    get_nym_res = await get_nym(pool_handle, wallet_handle, trustee_did, another_random_did)

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
    res = json.loads(await ledger.submit_request(pool_handle, req))
    assert res['op'] == 'REPLY'

    assert all([res['op'] == 'REPLY' for res in add_before_results])
    assert all([res['result']['seqNo'] is not None for res in get_after_results])
    assert nym_res['op'] == 'REPLY'
    assert get_nym_res['result']['seqNo'] is not None
    assert all([check is not -1 for check in version_checks])
    assert all([check is not -1 for check in status_checks])
