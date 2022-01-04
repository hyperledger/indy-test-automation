import pytest
import asyncio
from system.utils import *
import docker
from system.docker_setup import NETWORK_NAME


WRITE_READ_TIMEOUT = 360


@pytest.mark.usefixtures('docker_setup_and_teardown')
@pytest.mark.usefixtures('check_no_failures_fixture')
class TestCatchUpSuiteExtended:

    # @pytest.mark.parametrize(
    #     'check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count',
    #     [
    #         (True, False, 25, 0),
    #         (False, True, 25, 200),
    #         (False, False, 25, 200)
    #     ]
    # )
    # @pytest.mark.nodes_num(8)
    # @pytest.mark.asyncio
    # async def test_case_token_ledger(
    #         self, payment_init, initial_token_minting, pool_handler, wallet_handler, get_default_trustee, nodes_num,
    #         check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count
    # ):
    #     trustee_did, _ = get_default_trustee
    #     test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
    #     address1 = initial_token_minting
    #     await ensure_pool_is_in_sync(nodes_num=nodes_num)

    #     test_nodes[-1].stop_service()
    #     await send_payments(pool_handler, wallet_handler, trustee_did, address1, main_txn_count)

    #     test_nodes[-1].start_service()
    #     if check_reachability:
    #         await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
    #     if wait_catchup_before_ordering:
    #         await ensure_pool_is_in_sync(nodes_num=nodes_num)
    #     await send_payments(pool_handler, wallet_handler, trustee_did, address1, main_txn_count)

    #     if extra_txn_count != 0:  # force catchup
    #         await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
    #         await ensure_pool_performs_write_read(
    #             pool_handler, wallet_handler, trustee_did, nyms_count=extra_txn_count, timeout=WRITE_READ_TIMEOUT
    #         )

    #     await ensure_pool_is_in_sync(nodes_num=nodes_num)
    #     await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize(
        'check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count, is_single_nym',
        [
            # (True, False, 25, 0, False), skipped because of INDY-1960
            (True, False, 25, 0, True),  # use single STEWARD for all NODE txns instead of skipped case
            (False, True, 25, 200, False),
            (False, False, 25, 200, False)
        ]
    )
    @pytest.mark.nodes_num(8)
    @pytest.mark.asyncio
    async def test_case_pool_ledger(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num,
            check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count, is_single_nym
    ):
        trustee_did, _ = get_default_trustee
        if is_single_nym:
            alias = 'SomeNode'
        else:
            alias = None
        test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        test_nodes[-1].stop_service()
        await send_nodes(pool_handler, wallet_handler, trustee_did, main_txn_count, alias=alias)

        test_nodes[-1].start_service()
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await send_nodes(pool_handler, wallet_handler, trustee_did, main_txn_count, alias=alias)

        if extra_txn_count != 0:  # force catchup
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
            await ensure_pool_performs_write_read(
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
    @pytest.mark.nodes_num(8)
    @pytest.mark.asyncio
    async def test_case_config_ledger(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num,
            check_reachability, wait_catchup_before_ordering, main_txn_count, extra_txn_count
    ):
        trustee_did, _ = get_default_trustee
        test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
        await ensure_pool_is_in_sync(nodes_num=nodes_num)

        test_nodes[-1].stop_service()
        await send_upgrades(pool_handler, wallet_handler, trustee_did, 'indy-node', main_txn_count)

        test_nodes[-1].start_service()
        if check_reachability:
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        if wait_catchup_before_ordering:
            await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await send_upgrades(pool_handler, wallet_handler, trustee_did, 'indy-node', main_txn_count)

        if extra_txn_count != 0:  # force catchup
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
            await ensure_pool_performs_write_read(
                pool_handler, wallet_handler, trustee_did, nyms_count=extra_txn_count, timeout=WRITE_READ_TIMEOUT
            )

        await ensure_pool_is_in_sync(nodes_num=nodes_num)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
