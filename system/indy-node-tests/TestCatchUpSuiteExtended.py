import pytest
import asyncio
from system.utils import *
import docker
from system.docker_setup import NETWORK_NAME


WRITE_READ_TIMEOUT = 300


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestCatchUpSuiteExtended:

    @pytest.mark.parametrize(
        'wait_catchup_before_ordering, main_txn_count, extra_txn_count',
        [
            # (True, 55, 0),  # wait for catchup subcase
            # (False, 10, 0),  # less than 100 requests total subcase
            (False, 55, 200)  # send extra requests to force catchup subcase
        ]
    )
    @pytest.mark.nodes_num(8)
    @pytest.mark.asyncio
    async def test_case_token_ledger(
            self, payment_init, initial_token_minting, pool_handler, wallet_handler, get_default_trustee, nodes_num,
            wait_catchup_before_ordering, main_txn_count, extra_txn_count,
            check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
        address1 = initial_token_minting
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        test_nodes[-1].stop_service()
        await send_payments(pool_handler, wallet_handler, trustee_did, address1, main_txn_count)

        test_nodes[-1].start_service()
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await send_payments(pool_handler, wallet_handler, trustee_did, address1, main_txn_count)

        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=extra_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize(
        'wait_catchup_before_ordering, main_txn_count, extra_txn_count',
        [
            # (True, 55, 0),  # wait for catchup subcase
            # (False, 10, 0),  # less than 100 requests total subcase
            (False, 55, 200)  # send extra requests to force catchup subcase
        ]
    )
    @pytest.mark.nodes_num(8)
    @pytest.mark.asyncio
    async def test_case_pool_ledger(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num,
            wait_catchup_before_ordering, main_txn_count, extra_txn_count,
            check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        test_nodes[-1].stop_service()
        await send_nodes(pool_handler, wallet_handler, trustee_did, main_txn_count)

        test_nodes[-1].start_service()
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await send_nodes(pool_handler, wallet_handler, trustee_did, main_txn_count)

        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=extra_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize(
        'wait_catchup_before_ordering, main_txn_count, extra_txn_count',
        [
            # (True, 55, 0),  # wait for catchup subcase
            # (False, 10, 0),  # less than 100 requests total subcase
            (False, 55, 200),  # send extra requests to force catchup subcase
            # (False, 55, 0)  # special subcase for config !!!
        ]
    )
    @pytest.mark.nodes_num(8)
    @pytest.mark.asyncio
    async def test_case_config_ledger(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num,
            wait_catchup_before_ordering, main_txn_count, extra_txn_count,
            check_no_failures_fixture
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        test_nodes[-1].stop_service()
        await send_upgrades(pool_handler, wallet_handler, trustee_did, 'indy-node', main_txn_count)

        test_nodes[-1].start_service()
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await send_upgrades(pool_handler, wallet_handler, trustee_did, 'indy-node', main_txn_count)

        await ensure_pool_performs_write_read(
            pool_handler, wallet_handler, trustee_did, nyms_count=extra_txn_count, timeout=WRITE_READ_TIMEOUT
        )

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
