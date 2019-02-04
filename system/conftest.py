import pytest
import testinfra
from utils import *
from indy import *
from async_generator import yield_, async_generator
import time
from random import sample, shuffle
from json import JSONDecodeError


@pytest.fixture()
@async_generator
async def pool_handler():
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    await yield_(pool_handle)


@pytest.fixture()
@async_generator
async def wallet_handler():
    wallet_handle, _, _ = await wallet_helper()
    await yield_(wallet_handle)


@pytest.fixture()
@async_generator
async def get_default_trustee(wallet_handler):
    trustee_did, trustee_vk = await default_trustee(wallet_handler)
    await yield_((trustee_did, trustee_vk))


@pytest.fixture()
@async_generator
async def send_and_get_nyms_before_and_after(get_default_trustee, pool_handler, wallet_handler, check_ledger_sync):
    trustee_did, _ = get_default_trustee
    random_did = random_did_and_json()[0]
    another_random_did = random_did_and_json()[0]

    add_before = await nym_helper(pool_handler, wallet_handler, trustee_did, random_did)
    assert add_before['op'] == 'REPLY'
    get_before = await get_nym_helper(pool_handler, wallet_handler, trustee_did, random_did)
    assert get_before['result']['seqNo'] is not None
    print('\nSEND AND GET NYM SETUP IS DONE!')

    await yield_()

    add_after = await nym_helper(pool_handler, wallet_handler, trustee_did, another_random_did)
    assert add_after['op'] == 'REPLY'
    get_after = await get_nym_helper(pool_handler, wallet_handler, trustee_did, another_random_did)
    time.sleep(5)
    get_after_backup = await get_nym_helper(pool_handler, wallet_handler, trustee_did, another_random_did)
    assert (get_after['result']['seqNo'] | get_after_backup['result']['seqNo']) is not None
    print('\nSEND AND GET NYM TEARDOWN IS DONE!')


@pytest.fixture()
@async_generator
async def stop_and_start_primary(get_default_trustee, pool_handler, wallet_handler):
    trustee_did, _ = get_default_trustee

    req = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    try:
        result = json.loads(sample(results.items(), 1)[0][1])
    except JSONDecodeError:
        try:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
        except JSONDecodeError:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
    name_before = result['result']['data']['Node_info']['Name']
    primary_before =\
        result['result']['data']['Node_info']['Replicas_status'][name_before+':0']['Primary'][len('Node'):-len(':0')]
    host = testinfra.get_host('docker://node'+primary_before)
    host.run('systemctl stop indy-node')
    print('\nPRIMARY NODE {} HAS BEEN STOPPED!'.format(primary_before))

    await yield_()

    host.run('systemctl start indy-node')
    req = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
    try:
        result = json.loads(sample(results.items(), 1)[0][1])
    except JSONDecodeError:
        try:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
        except JSONDecodeError:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
    name_after = result['result']['data']['Node_info']['Name']
    primary_after =\
        result['result']['data']['Node_info']['Replicas_status'][name_after+':0']['Primary'][len('Node'):-len(':0')]
    print('\nEX-PRIMARY NODE HAS BEEN STARTED!')
    print('\nNEW PRIMARY IS {}'.format(primary_after))

    assert primary_before != primary_after


@pytest.fixture()
@async_generator
async def demote_and_promote_primary(get_default_trustee, pool_handler, wallet_handler):
    trustee_did, _ = get_default_trustee

    req_vi = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req_vi))
    try:
        result = json.loads(sample(results.items(), 1)[0][1])
    except JSONDecodeError:
        try:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
        except JSONDecodeError:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
    name_before = result['result']['data']['Node_info']['Name']
    primary_before =\
        result['result']['data']['Node_info']['Replicas_status'][name_before+':0']['Primary'][len('Node'):-len(':0')]
    res = json.loads(results['Node'+primary_before])
    target_did = res['result']['data']['Node_info']['did']
    alias = res['result']['data']['Node_info']['Name']
    demote_data = json.dumps({'alias': alias, 'services': []})
    demote_req = await ledger.build_node_request(trustee_did, target_did, demote_data)
    demote_res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, demote_req))
    assert demote_res['op'] == 'REPLY'
    print('\nPRIMARY NODE {} HAS BEEN DEMOTED!'.format(primary_before))

    await yield_()

    promote_data = json.dumps({'alias': alias, 'services': ['VALIDATOR']})
    promote_req = await ledger.build_node_request(trustee_did, target_did, promote_data)
    promote_res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, promote_req))
    host = testinfra.get_host('docker://node'+primary_before)
    host.run('systemctl restart indy-node')
    assert promote_res['op'] == 'REPLY'
    print('\nEX-PRIMARY NODE HAS BEEN PROMOTED AND RESTARTED!')

    results = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req_vi))
    try:
        result = json.loads(sample(results.items(), 1)[0][1])
    except JSONDecodeError:
        try:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
        except JSONDecodeError:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
    name_after = result['result']['data']['Node_info']['Name']
    primary_after =\
        result['result']['data']['Node_info']['Replicas_status'][name_after+':0']['Primary'][len('Node'):-len(':0')]
    print('\nNEW PRIMARY IS {}'.format(primary_after))

    assert primary_before != primary_after


@pytest.fixture()
@async_generator
async def check_ledger_sync(get_default_trustee, pool_handler, wallet_handler):

    await yield_()

    time.sleep(10)
    hosts = [testinfra.get_host('docker://node{}'.format(i)) for i in range(1, 5)]
    results = [host.run('read_ledger --type=domain --count') for host in hosts]
    assert all([results[i].stdout == results[i+1].stdout for i in range(-1, len(results)-1)])
    print('\nLEDGER SYNC TEARDOWN: {}'.format([result.stdout for result in results]))
