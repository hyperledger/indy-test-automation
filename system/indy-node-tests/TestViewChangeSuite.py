import pytest
import asyncio
from system.utils import *


@pytest.mark.usefixtures('docker_setup_and_teardown')
@pytest.mark.usefixtures('check_no_failures_fixture')
class TestViewChangeSuite:

    @pytest.mark.asyncio
    async def test_vc_by_restart_primary(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num
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

    @pytest.mark.skip('INDY-2023')
    @pytest.mark.asyncio
    async def test_vc_by_demotion_primary(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        trustee_did, _ = get_default_trustee
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

        primary_before, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)
        primary_next = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_before)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

        await eventually(promote_node, pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_next)

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize('node_id', [2, 7])
    @pytest.mark.asyncio
    async def test_vc_by_demotion_exact(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num, node_id
    ):
        trustee_did, _ = get_default_trustee
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

        pool_info = get_pool_info('1')
        _alias = get_node_alias(node_id)
        _did = get_node_did(_alias, pool_info=pool_info)

        primary_first, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, _alias, _did)
        primary_next = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_first)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

        await eventually(promote_node, pool_handler, wallet_handler, trustee_did, _alias, _did)
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_next)

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.nodes_num(8)
    @pytest.mark.asyncio
    async def test_demotion_of_backup_primary_with_restart_with_vc(
        self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        R0_PRIMARY_ID = 1
        R1_PRIMARY_ID = 2
        R2_PRIMARY_ID = 3

        hosts = [NodeHost(node_id + 1) for node_id in range(nodes_num)]
        trustee_did, _ = get_default_trustee
        await check_pool_is_functional(pool_handler, wallet_handler, trustee_did)

        pool_info = get_pool_info(str(R0_PRIMARY_ID))

        primary_r2_alias = get_node_alias(R2_PRIMARY_ID)
        primary_r2_did = get_node_did(primary_r2_alias, pool_info=pool_info)
        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, primary_r2_alias, primary_r2_did)

        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, str(R0_PRIMARY_ID))
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

        restart_pool(hosts)

        await ensure_pool_is_in_sync(node_ids=[h.id for h in hosts if h.id != R2_PRIMARY_ID])
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.nodes_num(8)
    @pytest.mark.asyncio
    async def test_demotion_of_backup_primary_with_restart_without_vc(
        self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        R0_PRIMARY_ID = 1
        R1_PRIMARY_ID = 2
        R2_PRIMARY_ID = 3

        hosts = [NodeHost(node_id + 1) for node_id in range(nodes_num)]
        trustee_did, _ = get_default_trustee
        await check_pool_is_functional(pool_handler, wallet_handler, trustee_did)

        pool_info = get_pool_info(str(R0_PRIMARY_ID))
        host2 = hosts[R1_PRIMARY_ID - 1]
        host2.stop_service()

        primary_r2_alias = get_node_alias(R2_PRIMARY_ID)
        primary_r2_did = get_node_did(primary_r2_alias, pool_info=pool_info)
        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, primary_r2_alias, primary_r2_did)

        restart_pool(hosts)

        await ensure_pool_is_in_sync(node_ids=[h.id for h in hosts if h.id != R2_PRIMARY_ID])
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.nodes_num(4)
    @pytest.mark.asyncio
    async def test_multiple_vcs(
        self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        trustee_did, _ = get_default_trustee

        for i in range(10):
            primary, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
            p = NodeHost(primary)
            p.stop_service()
            await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
            await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
            p.start_service()

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize(
        'node_txns_count, loops_count, concurrency', [
            (15, 3, False),
            (10, 5, False),
            (5, 7, False),
            (150, 3, True),
            (100, 5, True),
            (50, 7, True)
        ]
    )
    @pytest.mark.nodes_num(5)
    @pytest.mark.asyncio
    async def test_misc_node_and_vc_interleaved(
        self, pool_handler, wallet_handler, get_default_trustee, nodes_num, node_txns_count, loops_count, concurrency
    ):
        trustee_did, _ = get_default_trustee
        pool_info = get_pool_info('1')

        for i in range(loops_count):
            # find primary
            primary, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
            # demote it to force VC
            await eventually(
                demote_node, pool_handler, wallet_handler, trustee_did, 'Node{}'.format(primary),
                pool_info['Node{}'.format(primary)], timeout=60
            )
            await pool.refresh_pool_ledger(pool_handler)
            # check VC status
            await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
            # send extra node txns
            if concurrency:  # send all txns at once concurrently
                tasks = []
                for _ in range(node_txns_count):
                    task = send_nodes(
                        pool_handler, wallet_handler, trustee_did, count=1, alias='INACTIVE_NODE'
                    )
                    tasks.append(task)
                await asyncio.gather(*tasks, return_exceptions=True)
            else:  # send all txns one by one
                await eventually(
                    send_nodes, pool_handler, wallet_handler, trustee_did, count=node_txns_count, alias='INACTIVE_NODE'
                )
            # promote ex-primary back
            await eventually(promote_node, pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)

        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=10)
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
