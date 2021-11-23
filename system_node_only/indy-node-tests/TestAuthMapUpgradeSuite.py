import pytest
import asyncio
from system.utils import *
import hashlib
from datetime import datetime, timedelta, timezone


import logging
logger = logging.getLogger(__name__)


@pytest.mark.parametrize('adder_role, adder_role_num', [
    ('TRUSTEE', '0'),
    ('STEWARD', '2'),
    ('TRUST_ANCHOR', '101'),
    ('NETWORK_MONITOR', '201')
])
@pytest.mark.parametrize('editor_role, editor_role_num', [
    ('NETWORK_MONITOR', '201'),
    ('TRUST_ANCHOR', '101'),
    ('STEWARD', '2'),
    ('TRUSTEE', '0')
])
@pytest.mark.asyncio
async def test_case_pool_upgrade(
        docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee,
        adder_role, adder_role_num, editor_role, editor_role_num):
    trustee_did, _ = get_default_trustee
    # add adder to start pool upgrade
    adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
    assert res['op'] == 'REPLY'
    # add editor to cancel pool upgrade
    editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
    assert res['op'] == 'REPLY'
    # set rule for adding
    req = await ledger.build_auth_rule_request(trustee_did, '109', 'ADD', 'action', '*', 'start',
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
    # set rule for editing
    req = await ledger.build_auth_rule_request(trustee_did, '109', 'EDIT', 'action', 'start', 'cancel',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': editor_role_num,
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {}
                                               }))
    res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    print(res3)
    assert res3['op'] == 'REPLY'
    # start pool upgrade
    init_time = 30
    version = '1.99.999'
    name = 'upgrade' + '_' + version + '_' + datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
    _sha256 = hashlib.sha256().hexdigest()
    _timeout = 5
    reinstall = False
    force = False
    package = 'indy-node'
    dests = ['Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv', '8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb',
             'DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya', '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA',
             '4SWokCJWJc69Tn74VvLS6t2G2ucvXqM9FDMsWJjmsUxe', 'Cv1Ehj43DDM5ttNBmC6VPpEfwXWwfGktHwjDJsTV5Fz8',
             'BM8dTooz5uykCbYSAAFwKNkYfT4koomBHsSWHTDtkjhW']
    docker_7_schedule = json.dumps(
        dict({dest: datetime.strftime(
            datetime.now(tz=timezone.utc) + timedelta(minutes=init_time + i * 5), '%Y-%m-%dT%H:%M:%S%z'
        ) for dest, i in zip(dests, range(len(dests)))})
    )
    req = await ledger.build_pool_upgrade_request(
        adder_did, name, version, 'start', _sha256, _timeout, docker_7_schedule, None, reinstall, force, package
    )
    res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
    print(res4)
    assert res4['op'] == 'REPLY'
    # cancel pool upgrade
    req = await ledger.build_pool_upgrade_request(
        editor_did, name, version, 'cancel', _sha256, _timeout, docker_7_schedule, None, reinstall, force, package
    )
    res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, editor_did, req))
    print(res5)
    assert res5['op'] == 'REPLY'
