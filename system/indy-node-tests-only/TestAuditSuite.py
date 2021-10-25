import pytest
import asyncio
from system.utils import *

import logging
logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestAuditSuite:

    @pytest.mark.asyncio
    async def test_case_restart_one_node(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        test_nodes[5].restart_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        primary2 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
        p2 = NodeHost(primary2)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        test_nodes[5].restart_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        p1.start_service()
        p2.stop_service()
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary2)
        test_nodes[5].stop_service()
        p2.start_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        test_nodes[5].start_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize('node_num_shift', [0, 1, 5])
    @pytest.mark.asyncio
    async def test_case_restart_master_backup_non_primary(
            self, pool_handler, wallet_handler, get_default_trustee, node_num_shift, nodes_num,
            check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        primary2 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        p1.start_service()
        next_node = NodeHost(int(primary2) + node_num_shift)
        next_node.restart_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.asyncio
    async def test_case_restart_all_nodes_at_the_same_time(
        self, pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]

        logger.info("1: Initiating a view change by stopping master primary")
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()

        logger.info("2: Ensure that primary has been changed")
        primary2 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)

        logger.info("3: Ensure pool works")
        await check_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=15)
        p1.start_service()

        logger.info("4: Restarting the pool")
        restart_pool(test_nodes)

        logger.info("5: Ensure pool is in sync")
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        logger.info("6: Ensure that primary has not been changed")
        primary_after_restart, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        assert primary_after_restart == primary2

        logger.info("7: Ensure pool works")
        await ensure_pool_is_functional(
            pool_handler, wallet_handler, trustee_did, nyms_count=30
        )

    @pytest.mark.asyncio
    async def test_case_restart_f_nodes(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        p1.start_service()
        for node in test_nodes[5:]:
            node.restart_service()
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.asyncio
    async def test_case_restart_n_minus_f_minus_one_nodes(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        p1.start_service()
        for node in test_nodes[3:]:
            node.restart_service()
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.asyncio
    async def test_case_restart_all_nodes_one_by_one(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num, check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        p1.start_service()
        for node in test_nodes:
            node.restart_service()
            # do not remove/change with eventually - it is sequential node stopping
            await asyncio.sleep(10)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize('node_num_shift', [0, 1, 5])
    @pytest.mark.asyncio
    async def test_case_demote_master_backup_non_primary(
            self, pool_handler, wallet_handler, get_default_trustee, node_num_shift, nodes_num,
            check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        primary1, alias1, target_did1 = await get_primary(pool_handler, wallet_handler, trustee_did)
        print('Primary at the beginning is {}'.format(primary1))
        p1 = NodeHost(primary1)
        p1.stop_service()
        primary2 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
        print('Primary after service stop is {}'.format(primary2))
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        p1.start_service()
        primary, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        print('Primary after service start is {}'.format(primary))
        # demote master primary / backup primary / non primary here
        alias_for_demotion = 'Node{}'.format(int(primary2)+node_num_shift)
        print(alias_for_demotion)
        target_did_for_demotion = get_pool_info(primary2)[alias_for_demotion]
        print(target_did_for_demotion)
        primary, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        print('Primary before demotion is {}'.format(primary))
        await eventually(
            demote_node, pool_handler, wallet_handler, trustee_did, alias_for_demotion, target_did_for_demotion
        )
        primary3 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary2)
        print('Primary after demotion is {}'.format(primary3))
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        await eventually(
            promote_node, pool_handler, wallet_handler, trustee_did, alias_for_demotion, target_did_for_demotion
        )
        primary4 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary3)
        print('Primary after promotion is {}'.format(primary4))
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

