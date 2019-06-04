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
async def test_vc_by_restart(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    primary_before, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
    print('\nPrimary before: {}'.format(primary_before))
    p1 = NodeHost(primary_before)
    p1.stop_service()
    primary_after = await wait_until_vc_is_done(primary_before, pool_handler, wallet_handler, trustee_did)
    print('\nPrimary after: {}'.format(primary_after))
    assert primary_before != primary_after
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
    p1.start_service()
    await eventually_positive(check_ledger_sync)


@pytest.mark.asyncio
async def test_vc_by_demotion(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    primary_before, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
    print('\nPrimary before: {}'.format(primary_before))
    await eventually_positive(demote_node, pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)
    primary_after = await wait_until_vc_is_done(primary_before, pool_handler, wallet_handler, trustee_did)
    print('\nPrimary after: {}'.format(primary_after))
    assert primary_before != primary_after
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
    await eventually_positive(promote_node, pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)
    await eventually_positive(check_ledger_sync)
