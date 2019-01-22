import testinfra
import pytest
import time
from utils import *
from indy import did, ledger


@pytest.mark.asyncio
async def test_vc_by_restart(simple):
    pool_handle, wallet_handle = simple
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    random_did = random_did_and_json()[0]
    another_random_did = random_did_and_json()[0]

    add_before = await nym_helper(pool_handle, wallet_handle, trustee_did, random_did)
    assert add_before['op'] == 'REPLY'
    time.sleep(3)
    get_before = await get_nym_helper(pool_handle, wallet_handle, trustee_did, random_did)
    assert get_before['result']['seqNo'] is not None

    req = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    result = json.loads(results['Node4'])
    primary_before =\
        result['result']['data']['Node_info']['Replicas_status']['Node4:0']['Primary'][len('Node'):-len(':0')]
    host = testinfra.get_host('docker://node'+primary_before)
    host.run('systemctl stop indy-node')

    time.sleep(120)

    add_after = await nym_helper(pool_handle, wallet_handle, trustee_did, another_random_did)
    assert add_after['op'] == 'REPLY'
    time.sleep(3)
    get_after = await get_nym_helper(pool_handle, wallet_handle, trustee_did, another_random_did)
    assert get_after['result']['seqNo'] is not None

    print(add_after, '\n', get_after)

    req = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    result = json.loads(results['Node4'])
    primary_after =\
        result['result']['data']['Node_info']['Replicas_status']['Node4:0']['Primary'][len('Node'):-len(':0')]
    host.run('systemctl start indy-node')

    assert primary_before != primary_after

    print(primary_before)
    print(primary_after)


@pytest.mark.asyncio
async def test_vc_by_demotion(simple):
    pool_handle, wallet_handle = simple
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    random_did = random_did_and_json()[0]
    another_random_did = random_did_and_json()[0]

    add_before = await nym_helper(pool_handle, wallet_handle, trustee_did, random_did)
    time.sleep(3)
    get_before = await get_nym_helper(pool_handle, wallet_handle, trustee_did, random_did)

    print(add_before, '\n', get_before)

    req_vi = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req_vi))
    result = json.loads(results['Node4'])
    primary_before =\
        result['result']['data']['Node_info']['Replicas_status']['Node4:0']['Primary'][len('Node'):-len(':0')]
    res = json.loads(results['Node'+primary_before])
    target_did = res['result']['data']['Node_info']['did']
    alias = res['result']['data']['Node_info']['Name']
    demote_data = json.dumps({'alias': alias, 'services': []})
    demote_req = await ledger.build_node_request(trustee_did, target_did, demote_data)
    demote_res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, demote_req))
    assert demote_res['op'] == 'REPLY'

    time.sleep(120)

    add_after = await nym_helper(pool_handle, wallet_handle, trustee_did, another_random_did)
    time.sleep(3)
    get_after = await get_nym_helper(pool_handle, wallet_handle, trustee_did, another_random_did)

    print(add_after, '\n', get_after)

    promote_data = json.dumps({'alias': alias, 'services': ['VALIDATOR']})
    promote_req = await ledger.build_node_request(trustee_did, target_did, promote_data)
    promote_res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, promote_req))
    assert promote_res['op'] == 'REPLY'

    results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req_vi))
    result = json.loads(results['Node4'])
    primary_after =\
        result['result']['data']['Node_info']['Replicas_status']['Node4:0']['Primary'][len('Node'):-len(':0')]

    assert add_before['op'] == 'REPLY'
    assert get_before['result']['seqNo'] is not None
    assert add_after['op'] == 'REPLY'
    assert get_after['result']['seqNo'] is not None
    assert primary_before != primary_after

    print(primary_before)
    print(primary_after)
