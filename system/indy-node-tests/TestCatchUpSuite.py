import pytest
import asyncio
from system.utils import *
import docker
from system.docker_setup import NETWORK_NAME


WRITE_READ_TIMEOUT = 360


@pytest.mark.usefixtures('docker_setup_and_teardown')
@pytest.mark.usefixtures('check_no_failures_fixture')
class TestCatchUpSuite:

    @pytest.mark.parametrize(
        'check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count',
        [
            (True, False, 25, 0),
            (False, True, 25, 200),
            (False, False, 25, 200)
        ]
    )
    @pytest.mark.nodes_num(9)
    @pytest.mark.asyncio
    async def test_case_stopping(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num,
            check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        test_nodes[-1].stop_service()
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        test_nodes[-2].stop_service()
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        test_nodes[-2].start_service()
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did, unreached=1)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num-1)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        test_nodes[-1].start_service()
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        if extra_txn_count != 0:  # force catchup
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
            await ensure_pool_is_functional(
                pool_handler, wallet_handler, trustee_did, nyms_count=extra_txn_count, timeout=WRITE_READ_TIMEOUT
            )
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize(
        'check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count',
        [
            (True, False, 25, 0),
            (False, True, 25, 200),
            (False, False, 25, 200)
        ]
    )
    @pytest.mark.nodes_num(9)
    @pytest.mark.asyncio
    async def test_case_demoting(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num,
            check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count
    ):
        trustee_did, _ = get_default_trustee
        pool_info = get_pool_info('1')
        print('\nPOOL INFO:\n{}'.format(pool_info))
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, 'Node9', pool_info['Node9'])
        await pool.refresh_pool_ledger(pool_handler)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, 'Node8', pool_info['Node8'])
        await pool.refresh_pool_ledger(pool_handler)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        await eventually(promote_node, pool_handler, wallet_handler, trustee_did, 'Node8', pool_info['Node8'])
        await pool.refresh_pool_ledger(pool_handler)
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num-1)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        await eventually(promote_node, pool_handler, wallet_handler, trustee_did, 'Node9', pool_info['Node9'])
        await pool.refresh_pool_ledger(pool_handler)
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        if extra_txn_count != 0:  # force catchup
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
            await ensure_pool_is_functional(
                pool_handler, wallet_handler, trustee_did, nyms_count=extra_txn_count, timeout=WRITE_READ_TIMEOUT
            )
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize(
        'check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count',
        [
            (True, False, 25, 0),
            (False, True, 25, 200),
            (False, False, 25, 200)
        ]
    )
    @pytest.mark.nodes_num(9)
    @pytest.mark.asyncio
    async def test_case_out_of_network(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num,
            check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count
    ):
        client = docker.from_env()
        trustee_did, _ = get_default_trustee
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        client.networks.list(names=[NETWORK_NAME])[0].disconnect('node9')
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        client.networks.list(names=[NETWORK_NAME])[0].disconnect('node8')
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        client.networks.list(names=[NETWORK_NAME])[0].connect('node8')
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did, unreached=1)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num-1)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        client.networks.list(names=[NETWORK_NAME])[0].connect('node9')
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        if extra_txn_count != 0:  # force catchup
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
            await ensure_pool_is_functional(
                pool_handler, wallet_handler, trustee_did, nyms_count=extra_txn_count, timeout=WRITE_READ_TIMEOUT
            )
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize(
        'check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count',
        [
            (True, False, 25, 0),
            (False, True, 25, 200),
            (False, False, 25, 200)
        ]
    )
    @pytest.mark.nodes_num(9)
    @pytest.mark.asyncio
    async def test_case_switch_off_machines(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num,
            check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count
    ):
        client = docker.from_env()
        test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
        trustee_did, _ = get_default_trustee
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        client.containers.list(all=True, filters={'name': 'node9'})[0].stop()
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        client.containers.list(all=True, filters={'name': 'node8'})[0].stop()
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        client.containers.list(all=True, filters={'name': 'node8'})[0].start()
        await eventually(test_nodes[-2].start_service, timeout=30)
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did, unreached=1)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num-1)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        client.containers.list(all=True, filters={'name': 'node9'})[0].start()
        await eventually(test_nodes[-1].start_service, timeout=30)
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=main_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        if extra_txn_count != 0:  # force catchup
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
            await ensure_pool_is_functional(
                pool_handler, wallet_handler, trustee_did, nyms_count=extra_txn_count, timeout=WRITE_READ_TIMEOUT
            )
        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
