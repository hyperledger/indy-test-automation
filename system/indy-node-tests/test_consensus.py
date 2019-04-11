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
    is_exception_raised1 = await eventually_negative\
        (nym_helper, pool_handler, wallet_handler, trustee_did, did3, None, None, None)
    assert is_exception_raised1 is True
    res1 = await eventually_positive(get_nym_helper, pool_handler, wallet_handler, trustee_did, did1, is_reading=True)
    assert res1['result']['seqNo'] is not None
    # 3/7 online - can r only
    output = hosts[3].check_output('systemctl stop indy-node')
    print(output)
    is_exception_raised2 = await eventually_negative\
        (nym_helper, pool_handler, wallet_handler, trustee_did, did4, None, None, None)
    assert is_exception_raised2 is True
    res2 = await eventually_positive(get_nym_helper, pool_handler, wallet_handler, trustee_did, did2, is_reading=True)
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
    # Stop all except 1
    outputs = [host.check_output('systemctl stop indy-node') for host in hosts[1:]]
    print(outputs)
    res = await eventually_positive(get_nym_helper, pool_handler, wallet_handler, trustee_did, did1, is_reading=True)
    assert res['result']['seqNo'] is not None
    # Stop the last one
    hosts[0].check_output('systemctl stop indy-node')
    # Start all
    outputs = [host.check_output('systemctl start indy-node') for host in hosts]
    print(outputs)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)


@pytest.mark.asyncio
async def test_consensus_n_and_f_changing(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did3, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    hosts = [testinfra.get_host('ssh://node' + str(i)) for i in range(1, 8)]

    primary1, alias1, target_did1 = await get_primary(pool_handler, wallet_handler, trustee_did)
    alias, target_did = await demote_random_node(pool_handler, wallet_handler, trustee_did)
    primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
    assert primary2 != primary1
    temp_hosts = hosts.copy()
    temp_hosts.pop(int(alias[4:])-1)
    outputs = [host.check_output('systemctl stop indy-node') for host in temp_hosts[-2:]]
    print(outputs)
    is_exception_raised1 = await eventually_negative\
        (nym_helper, pool_handler, wallet_handler, trustee_did, did1, None, None, None)
    assert is_exception_raised1 is True
    outputs = [host.check_output('systemctl start indy-node') for host in temp_hosts[-2:]]
    print(outputs)
    # primary3 = await wait_until_vc_is_done(primary2, pool_handler, wallet_handler, trustee_did)
    # assert primary3 != primary2
    await eventually_positive\
        (promote_node, pool_handler, wallet_handler, trustee_did, alias, target_did, is_self_asserted=True)
    outputs = [host.check_output('systemctl stop indy-node') for host in hosts[-2:]]
    print(outputs)
    primary4 = await wait_until_vc_is_done(primary2, pool_handler, wallet_handler, trustee_did)
    assert primary4 != primary2
    res2 = await eventually_positive(nym_helper, pool_handler, wallet_handler, trustee_did, did2, None, None, None)
    assert res2['op'] == 'REPLY'
    output = hosts[0].check_output('systemctl stop indy-node')
    print(output)
    is_exception_raised2 = await eventually_negative\
        (nym_helper, pool_handler, wallet_handler, trustee_did, did3, None, None, None)
    assert is_exception_raised2 is True
    # Start all
    outputs = [host.check_output('systemctl start indy-node') for host in hosts]
    print(outputs)
