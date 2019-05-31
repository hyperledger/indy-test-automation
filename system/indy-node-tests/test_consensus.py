import pytest
import logging
from async_generator import async_generator

from system.utils import *
from system.docker_setup import setup_and_teardown

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=0, format='%(asctime)s %(message)s')

@pytest.fixture(scope='function', autouse=True)
@async_generator
async def docker_setup_and_teardown():
    await setup_and_teardown()


@pytest.mark.asyncio
async def test_consensus_restore_after_f_plus_one(pool_handler, wallet_handler,
                                                  get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did3, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did4, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    test_nodes = [NodeHost(i) for i in range(1, 8)]

    # 7/7 online - can w+r
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    # 5/7 online - can w+r
    for node in test_nodes[-2:]:
        node.stop_service()
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
    # 4/7 online - can r only
    test_nodes[4].stop_service()
    is_exception_raised1 = await eventually_negative\
        (send_nym, pool_handler, wallet_handler, trustee_did, did3, None, None, None)
    assert is_exception_raised1 is True
    res1 = await read_eventually_positive(get_nym, pool_handler, wallet_handler, trustee_did, did1)
    assert res1['result']['seqNo'] is not None
    # 3/7 online - can r only
    test_nodes[3].stop_service()
    is_exception_raised2 = await eventually_negative\
        (send_nym, pool_handler, wallet_handler, trustee_did, did4, None, None, None)
    assert is_exception_raised2 is True
    res2 = await read_eventually_positive(get_nym, pool_handler, wallet_handler, trustee_did, did2)
    assert res2['result']['seqNo'] is not None
    # 5/7 online - can w+r
    for node in test_nodes[3:5]:
        node.start_service()
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did3)
    # 7/7 online - can w+r
    for node in test_nodes[-2:]:
        node.start_service()
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did4)


@pytest.mark.asyncio
async def test_consensus_state_proof_reading(pool_handler, wallet_handler,
                                             get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    test_nodes = [NodeHost(i) for i in range(1, 8)]

    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    # Stop all except 1
    for node in test_nodes[1:]:
        node.stop_service()
    res = await read_eventually_positive(get_nym, pool_handler, wallet_handler, trustee_did, did1)
    assert res['result']['seqNo'] is not None
    # Stop the last one
    test_nodes[0].stop_service()
    # Start all
    for node in test_nodes:
        node.start_service()
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)


@pytest.mark.skip(reason='INDY-2059, INDY-2023')
@pytest.mark.asyncio
async def test_consensus_n_and_f_changing(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did3, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    test_nodes = [NodeHost(i) for i in range(1, 8)]

    primary1, alias1, target_did1 = await get_primary(pool_handler, wallet_handler, trustee_did)
    print('PRIMARY 1: {}'.format(primary1))
    alias, target_did = await demote_random_node(pool_handler, wallet_handler, trustee_did)
    primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
    print('PRIMARY 2: {}'.format(primary2))
    assert primary2 != primary1
    temp_test_nodes = test_nodes.copy()
    temp_test_nodes.pop(int(alias[4:])-1)
    for node in temp_test_nodes[-2:]:
        node.stop_service()
    is_exception_raised1 = await eventually_negative\
        (send_nym, pool_handler, wallet_handler, trustee_did, did1, None, None, None)
    assert is_exception_raised1 is True
    for node in temp_test_nodes[-2:]:
        node.start_service()
    await eventually_positive\
        (promote_node, pool_handler, wallet_handler, trustee_did, alias, target_did)
    for node in test_nodes[-2:]:
        node.stop_service()
    primary4 = await wait_until_vc_is_done(primary2, pool_handler, wallet_handler, trustee_did)
    print('PRIMARY 4: {}'.format(primary4))
    assert primary4 != primary2
    res2 = await write_eventually_positive(send_nym, pool_handler, wallet_handler, trustee_did, did2, None, None, None)
    assert res2['op'] == 'REPLY'
    test_nodes[0].stop_service()
    is_exception_raised2 = await eventually_negative\
        (send_nym, pool_handler, wallet_handler, trustee_did, did3, None, None, None)
    assert is_exception_raised2 is True
    # Start all
    for node in test_nodes:
        node.start_service()
