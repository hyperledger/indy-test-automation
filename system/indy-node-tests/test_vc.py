import pytest
import logging
import asyncio
from async_generator import async_generator, yield_

from system.utils import *

import logging
logger = logging.getLogger(__name__)

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=0, format='%(asctime)s %(message)s')


@pytest.fixture(scope='function', autouse=True)
@async_generator
async def docker_setup_and_teardown(docker_setup_and_teardown_function):
    await yield_()


@pytest.mark.asyncio
async def test_vc_by_restart(
        pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
):
    trustee_did, _ = get_default_trustee
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
    primary_before, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
    p1 = NodeHost(primary_before)
    p1.stop_service()
    await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_before)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
    p1.start_service()
    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)


@pytest.mark.asyncio
async def test_vc_by_demotion(
        pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
):
    trustee_did, _ = get_default_trustee
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
    primary_before, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
    await eventually(demote_node, pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)
    await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_before)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
    await eventually(promote_node, pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)
    await ensure_pool_is_in_sync(nodes_num=nodes_num)
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, timeout=360)


@pytest.mark.nodes_num(8)
@pytest.mark.asyncio
async def test_demotion_of_backup_primary_with_restart_with_vc(
    pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
):
    R0_PRIMARY_ID = 1
    R1_PRIMARY_ID = 2
    R2_PRIMARY_ID = 3

    hosts = [NodeHost(node_id + 1) for node_id in range(nodes_num)]
    trustee_did, _ = get_default_trustee

    logger.info("1 Have 8 nodes in the pool, so that primaries are [Node1, Node2, Node3]")
    await check_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    pool_info = get_pool_info(str(R0_PRIMARY_ID))

    logger.info("2 Demote primary for replica 2")

    primary_r2_alias = get_node_alias(R2_PRIMARY_ID)
    primary_r2_did = get_node_did(primary_r2_alias, pool_info=pool_info)
    await eventually(
        demote_node, pool_handler, wallet_handler, trustee_did, primary_r2_alias, primary_r2_did
    )

    logger.info("3 Wait for view change")
    # TODO timeouts
    logger.info('Primary before: {}'.format(R0_PRIMARY_ID))
    primary_after = await ensure_primary_changed(
        pool_handler, wallet_handler, trustee_did, str(R0_PRIMARY_ID)
    )
    logger.info('Primary after: {}'.format(primary_after))

    logger.info("4 Order 1 more txn")
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    logger.info("5 Restart the whole pool")
    restart_pool(hosts)

    logger.info("6 Make sure that the pool restarted correctly, and can order txns")

    logger.info("6.1 ensure that pool is in sync")
    # TODO timeouts
    await ensure_pool_is_in_sync(node_ids=[h.id for h in hosts if h.id != R2_PRIMARY_ID])

    logger.info("6.2 ensure that pool orders requests")
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, timeout=60)


@pytest.mark.nodes_num(8)
@pytest.mark.asyncio
async def test_demotion_of_backup_primary_with_restart_without_vc(
    pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
):
    R0_PRIMARY_ID = 1
    R1_PRIMARY_ID = 2
    R2_PRIMARY_ID = 3

    hosts = [NodeHost(node_id + 1) for node_id in range(nodes_num)]
    trustee_did, _ = get_default_trustee

    logger.info("1 Have 8 nodes in the pool, so that primaries are [Node1, Node2, Node3]")
    await check_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    logger.info("2 Stop Node2 to delay the view change to viewNo=1")
    pool_info = get_pool_info(str(R0_PRIMARY_ID))
    host2 = hosts[R1_PRIMARY_ID - 1]
    host2.stop_service()

    logger.info("3 Demote Node3: it will trigger a view change to viewNo=1")
    # which in turn will trigger a view change timeout since Node2 (the next primary)
    # has been stopped
    primary_r2_alias = get_node_alias(R2_PRIMARY_ID)
    primary_r2_did = get_node_did(primary_r2_alias, pool_info=pool_info)
    await eventually(
        demote_node, pool_handler, wallet_handler, trustee_did, primary_r2_alias, primary_r2_did
    )

    logger.info("4 Restart the whole pool right after Demote NODE txn is written on all nodes")
    restart_pool(hosts)

    logger.info("5 Make sure that the pool restarted correctly, and can order txns")
    logger.info("5.1 ensure that pool is in sync")
    # TODO timeouts
    await ensure_pool_is_in_sync(node_ids=[h.id for h in hosts if h.id != R2_PRIMARY_ID])

    logger.info("5.2 ensure that pool orders requests")
    await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, timeout=60)
