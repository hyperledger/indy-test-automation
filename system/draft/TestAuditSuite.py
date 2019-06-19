import pytest
import asyncio
from system.utils import *

import logging
logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestAuditSuite:

    @pytest.mark.asyncio
    async def test_case_restart_one_node(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 15)
        test_nodes[5].restart_service()
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually(check_pool_is_in_sync, timeout=60)
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
        p2 = NodeHost(primary2)
        assert primary2 != primary1
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 15)
        test_nodes[5].restart_service()
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        p1.start_service()
        p2.stop_service()
        primary3 = await wait_until_vc_is_done(primary2, pool_handler, wallet_handler, trustee_did)
        assert primary3 != primary2
        test_nodes[5].stop_service()
        p2.start_service()
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 15)
        test_nodes[5].start_service()
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually(check_pool_is_in_sync, timeout=60)
        await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])

    @pytest.mark.parametrize('node_num_shift', [0, 1, 5])
    @pytest.mark.asyncio
    async def test_case_restart_master_backup_non_primary(self, pool_handler, wallet_handler, get_default_trustee,
                                                          node_num_shift):
        trustee_did, _ = get_default_trustee
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
        assert primary2 != primary1
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 15)
        p1.start_service()
        next_node = NodeHost(int(primary2) + node_num_shift)
        next_node.restart_service()
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually(check_pool_is_in_sync, is_self_asserted=True)
        await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])

    @pytest.mark.asyncio
    async def test_case_restart_all_nodes_at_the_same_time(
        self, pool_handler, wallet_handler, get_default_trustee, nodes_num
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
    async def test_case_restart_f_nodes(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
        assert primary2 != primary1
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 15)
        p1.start_service()
        for node in test_nodes[5:]:
            node.restart_service()
        await asyncio.sleep(30)
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually(check_pool_is_in_sync, is_self_asserted=True)
        await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])

    @pytest.mark.asyncio
    async def test_case_restart_n_minus_f_minus_one_nodes(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
        assert primary2 != primary1
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 15)
        p1.start_service()
        for node in test_nodes[3:]:
            node.restart_service()
        await asyncio.sleep(30)
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually(check_pool_is_in_sync, is_self_asserted=True)
        await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])

    @pytest.mark.asyncio
    async def test_case_restart_all_nodes_one_by_one(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
        assert primary2 != primary1
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 15)
        p1.start_service()
        for node in test_nodes:
            node.restart_service()
            await asyncio.sleep(10)
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually(check_pool_is_in_sync, is_self_asserted=True)
        await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])

    @pytest.mark.parametrize('node_num_shift', [0, 1, 5])
    @pytest.mark.asyncio
    async def test_case_demote_master_backup_non_primary(self, pool_handler, wallet_handler, get_default_trustee,
                                                         node_num_shift):
        trustee_did, _ = get_default_trustee
        primary1, alias1, target_did1 = await get_primary(pool_handler, wallet_handler, trustee_did)
        p1 = NodeHost(primary1)
        p1.stop_service()
        primary2 = await wait_until_vc_is_done(primary1, pool_handler, wallet_handler, trustee_did)
        assert primary2 != primary1
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 15)
        p1.start_service()
        # demote master primary / backup primary / non primary here
        alias_for_demotion = 'Node{}'.format(int(primary2)+node_num_shift)
        print(alias_for_demotion)
        target_did_for_demotion = get_pool_info(primary2)[alias_for_demotion]
        print(target_did_for_demotion)
        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, alias_for_demotion,
                         target_did_for_demotion, is_self_asserted=True)
        primary3 = await wait_until_vc_is_done(primary2, pool_handler, wallet_handler, trustee_did)
        assert primary3 != primary2
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually(promote_node, pool_handler, wallet_handler, trustee_did, alias_for_demotion,
                         target_did_for_demotion, is_self_asserted=True)
        primary4 = await wait_until_vc_is_done(primary3, pool_handler, wallet_handler, trustee_did)
        assert primary4 != primary3
        await eventually(check_pool_is_in_sync, is_self_asserted=True)
        await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
