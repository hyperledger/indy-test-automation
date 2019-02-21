import pytest
from utils import *


@pytest.mark.asyncio
async def test_vc_by_restart(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1 = random_did_and_json()[0]
    did2 = random_did_and_json()[0]

    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    primary_before = await stop_primary(pool_handler, wallet_handler, trustee_did)

    time.sleep(120)

    primary_after = await start_primary(pool_handler, wallet_handler, trustee_did, primary_before)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
    time.sleep(20)
    check_ledger_sync()

    assert primary_before != primary_after


@pytest.mark.asyncio
async def test_vc_by_demotion(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1 = random_did_and_json()[0]
    did2 = random_did_and_json()[0]

    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    primary_before, target_did, alias = await demote_primary(pool_handler, wallet_handler, trustee_did)

    time.sleep(120)

    primary_after = await promote_primary(pool_handler, wallet_handler, trustee_did, primary_before, alias, target_did)
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
    time.sleep(20)
    check_ledger_sync()

    assert primary_before != primary_after
