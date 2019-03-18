import pytest
from system.utils import *
import logging
from indy import IndyError

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=0, format='%(asctime)s %(message)s')

# THIS TEST SUITE MUST BE RUN AGAINST 7 NODE POOL


@pytest.mark.asyncio
async def test_consensus_restore_after_f_plus_one(pool_handler, wallet_handler,
                                                  get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did3, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did4, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    hosts = [testinfra.get_host('ssh://node' + str(i)) for i in range(1, 8)]

    # 7/7 online - can w+r
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    # 5/7 online - can w+r
    outputs = [host.check_output('systemctl stop indy-node') for host in hosts[-2:]]
    print(outputs)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
    # 4/7 online - can r only
    output = hosts[4].check_output('systemctl stop indy-node')
    print(output)
    # time.sleep(60)
    # with pytest.raises(IndyError, match='Consensus is impossible'):
    while True:
        try:
            time.sleep(10)
            await nym_helper(pool_handler, wallet_handler, trustee_did, did3, None, None, None)
        except IndyError:
            print('EXPECTED INDY ERROR HAS BEEN RAISED')
            break
    res1 = await get_nym_helper(pool_handler, wallet_handler, trustee_did, did1)
    while res1['result']['seqNo'] is None:
        res1 = await get_nym_helper(pool_handler, wallet_handler, trustee_did, did1)
        time.sleep(1)
    assert res1['result']['seqNo'] is not None
    # 3/7 online - can r only
    output = hosts[3].check_output('systemctl stop indy-node')
    print(output)
    # with pytest.raises(IndyError, match='Consensus is impossible'):
    while True:
        try:
            time.sleep(10)
            await nym_helper(pool_handler, wallet_handler, trustee_did, did4, None, None, None)
        except IndyError:
            print('EXPECTED INDY ERROR HAS BEEN RAISED')
            break
    res2 = await get_nym_helper(pool_handler, wallet_handler, trustee_did, did2)
    while res2['result']['seqNo'] is None:
        res2 = await get_nym_helper(pool_handler, wallet_handler, trustee_did, did2)
        time.sleep(1)
    assert res2['result']['seqNo'] is not None
    # 5/7 online - can w+r
    outputs = [host.check_output('systemctl start indy-node') for host in hosts[3:5]]
    print(outputs)
    # time.sleep(90)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did3)
    # 7/7 online - can w+r
    outputs = [host.check_output('systemctl start indy-node') for host in hosts[-2:]]
    print(outputs)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did4)


@pytest.mark.asyncio
async def test_consensus_state_proof_reading(pool_handler, wallet_handler,
                                             get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    hosts = [testinfra.get_host('ssh://node' + str(i)) for i in range(1, 8)]

    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    # time.sleep(15)
    # Stop all except 1
    outputs = [host.check_output('systemctl stop indy-node') for host in hosts[1:]]
    print(outputs)
    # time.sleep(15)
    res = await get_nym_helper(pool_handler, wallet_handler, trustee_did, did1)
    while res['result']['seqNo'] is None:
        res = await get_nym_helper(pool_handler, wallet_handler, trustee_did, did1)
        time.sleep(1)
    assert res['result']['seqNo'] is not None
    # Stop the last one
    hosts[0].check_output('systemctl stop indy-node')
    # Start all
    outputs = [host.check_output('systemctl start indy-node') for host in hosts]
    print(outputs)
    # time.sleep(90)
    while True:
        try:
            time.sleep(10)
            await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
            print('NO ERRORS HERE SO BREAK THE LOOP')
            break
        except IndyError:
            pass


@pytest.mark.asyncio
async def test_consensus_n_and_f_changing(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did3, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    hosts = [testinfra.get_host('ssh://node' + str(i)) for i in range(1, 8)]

    alias, target_did = await demote_random_node(pool_handler, wallet_handler, trustee_did)
    temp_hosts = hosts.copy()
    temp_hosts.pop(int(alias[4:])-1)
    outputs = [host.check_output('systemctl stop indy-node') for host in temp_hosts[-2:]]
    print(outputs)
    # time.sleep(60)
    # with pytest.raises(IndyError, match='Consensus is impossible'):
    while True:
        try:
            time.sleep(10)
            await nym_helper(pool_handler, wallet_handler, trustee_did, did1, None, None, None)
        except IndyError:
            print('EXPECTED INDY ERROR HAS BEEN RAISED')
            break
    outputs = [host.check_output('systemctl start indy-node') for host in temp_hosts[-2:]]
    print(outputs)
    time.sleep(60)
    await promote_node(pool_handler, wallet_handler, trustee_did, alias, target_did)
    time.sleep(60)
    outputs = [host.check_output('systemctl stop indy-node') for host in hosts[-2:]]
    print(outputs)
    res2 = await nym_helper(pool_handler, wallet_handler, trustee_did, did2, None, None, None)
    while res2['op'] != 'REPLY':
        res2 = await nym_helper(pool_handler, wallet_handler, trustee_did, did2, None, None, None)
        time.sleep(1)
    assert res2['op'] == 'REPLY'
    output = hosts[0].check_output('systemctl stop indy-node')
    print(output)
    # time.sleep(60)
    # with pytest.raises(IndyError, match='Consensus is impossible'):
    while True:
        try:
            time.sleep(10)
            await nym_helper(pool_handler, wallet_handler, trustee_did, did3, None, None, None)
        except IndyError:
            print('EXPECTED INDY ERROR HAS BEEN RAISED')
            break
    # Start all
    outputs = [host.check_output('systemctl start indy-node') for host in hosts]
    print(outputs)
