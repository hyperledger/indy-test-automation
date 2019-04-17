import pytest
from system.utils import *


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestAuditSuite:

    @pytest.mark.asyncio
    async def test_case_restart_one_node(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, 8)]
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 15)
        test_nodes[5].restart_service()
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually_positive(check_ledger_sync)
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
        await eventually_positive(check_ledger_sync)
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
        await eventually_positive(check_ledger_sync)
        await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])

    @pytest.mark.asyncio
    async def test_case_restart_all_nodes_at_the_same_time(self, pool_handler, wallet_handler, get_default_trustee):
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
        primary3 = await wait_until_vc_is_done(primary2, pool_handler, wallet_handler, trustee_did)
        assert primary3 != primary2
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually_positive(check_ledger_sync)
        await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])

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
        time.sleep(30)
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually_positive(check_ledger_sync)
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
        time.sleep(30)
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually_positive(check_ledger_sync)
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
            time.sleep(10)
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually_positive(check_ledger_sync)
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
        await eventually_positive(demote_node, pool_handler, wallet_handler, trustee_did, alias_for_demotion,
                                  target_did_for_demotion)
        primary3 = await wait_until_vc_is_done(primary2, pool_handler, wallet_handler, trustee_did)
        assert primary3 != primary2
        await send_random_nyms(pool_handler, wallet_handler, trustee_did, 30)
        await eventually_positive(promote_node, pool_handler, wallet_handler, trustee_did, alias_for_demotion,
                                  target_did_for_demotion)
        time.sleep(60)
        await eventually_positive(check_ledger_sync)
        await send_and_get_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
