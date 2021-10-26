import pytest
import asyncio
from system.utils import *


@pytest.mark.usefixtures('docker_setup_and_teardown')
@pytest.mark.usefixtures('check_no_failures_fixture')
class TestConsensusSuite:

    @pytest.mark.asyncio
    async def test_consensus_restore_after_f_plus_one(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        responses = await check_pool_performs_write(pool_handler, wallet_handler, trustee_did, nyms_count=4)
        dids = [resp['result']['txn']['data']['dest'] for resp in responses]

        # 7/7 online - can w+r
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did)

        # 5/7 online - can w+r
        for node in test_nodes[-2:]:
            node.stop_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did)

        # 4/7 online - can r only
        test_nodes[4].stop_service()
        with pytest.raises(IndyError):
            await check_pool_performs_write(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        await check_pool_performs_read(pool_handler, wallet_handler, trustee_did, dids[:2])

        # 3/7 online - can r only
        test_nodes[3].stop_service()
        with pytest.raises(IndyError):
            await check_pool_performs_write(pool_handler, wallet_handler, trustee_did, nyms_count=5)
        await check_pool_performs_read(pool_handler, wallet_handler, trustee_did, dids[2:])

        # 5/7 online - can w+r
        for node in test_nodes[3:5]:
            node.start_service()
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did, unreached=2)
        await ensure_pool_is_in_sync(nodes_num=nodes_num-2)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did)

        # 7/7 online - can w+r
        for node in test_nodes[-2:]:
            node.start_service()
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.asyncio
    async def test_consensus_state_proof_reading(
            self, pool_handler, wallet_handler, get_default_trustee
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        responses = await check_pool_performs_write(pool_handler, wallet_handler, trustee_did, nyms_count=10)
        dids = [resp['result']['txn']['data']['dest'] for resp in responses]

        # Stop all except 1
        for node in test_nodes[1:]:
            node.stop_service()
        await check_pool_performs_read(pool_handler, wallet_handler, trustee_did, dids)

        # Start all
        for node in test_nodes:
            node.start_service()

        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.asyncio
    async def test_consensus_n_and_f_changing(
            self, pool_handler, wallet_handler, get_default_trustee
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]

        primary1, alias1, target_did1 = await get_primary(pool_handler, wallet_handler, trustee_did)
        alias, target_did = await demote_random_node(pool_handler, wallet_handler, trustee_did)
        primary2 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)

        temp_test_nodes = test_nodes.copy()
        temp_test_nodes.pop(int(alias[4:]) - 1)

        for node in temp_test_nodes[-2:]:
            node.stop_service()
        with pytest.raises(IndyError):
            await check_pool_performs_write(pool_handler, wallet_handler, trustee_did, nyms_count=5)

        for node in temp_test_nodes[-2:]:
            node.start_service()
        await eventually(
            promote_node, pool_handler, wallet_handler, trustee_did, alias, target_did, timeout=180
        )

        for node in test_nodes[-2:]:
            node.stop_service()
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary2)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did)

        test_nodes[0].stop_service()
        with pytest.raises(IndyError):
            await check_pool_performs_write(pool_handler, wallet_handler, trustee_did, nyms_count=5)

        # Start all
        for node in test_nodes:
            node.start_service()
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
