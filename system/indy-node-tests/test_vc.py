import pytest
from system.utils import *


@pytest.mark.asyncio
async def test_vc_by_restart(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    primary_before, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
    print('\nPrimary before: {}'.format(primary_before))
    host = testinfra.get_host('ssh://node'+primary_before)
    output = host.check_output('systemctl stop indy-node')
    print(output)
    primary_after = primary_before
    while primary_before == primary_after:
        primary_after, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        time.sleep(60)
    print('\nPrimary after: {}'.format(primary_after))
    assert primary_before != primary_after
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
    host = testinfra.get_host('ssh://node'+primary_before)
    output = host.check_output('systemctl start indy-node')
    print(output)
    time.sleep(30)
    check_ledger_sync()


@pytest.mark.asyncio
async def test_vc_by_demotion(pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    did1, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    did2, _ = await did.create_and_store_my_did(wallet_handler, '{}')
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did1)
    primary_before, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
    print('\nPrimary before: {}'.format(primary_before))
    await demote_node(pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)
    primary_after = primary_before
    while primary_before == primary_after:
        primary_after, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        time.sleep(60)
    print('\nPrimary after: {}'.format(primary_after))
    assert primary_before != primary_after
    await send_and_get_nym(pool_handler, wallet_handler, trustee_did, did2)
    await promote_node(pool_handler, wallet_handler, trustee_did, primary_alias, primary_did)
    time.sleep(30)
    check_ledger_sync()
