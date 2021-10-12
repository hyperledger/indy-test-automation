import pytest
from system.utils import *


@pytest.mark.asyncio
async def test_roles(docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    trustee1_did, trustee1_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    steward1_did, steward1_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    anchor1_did, anchor1_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    identity1_did, identity1_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    steward2_did, steward2_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    anchor2_did, anchor2_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    anchor3_did, anchor3_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    identity2_did, identity2_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    identity3_did, identity3_vk = await did.create_and_store_my_did(wallet_handler, '{}')
    identity4_did, identity4_vk = await did.create_and_store_my_did(wallet_handler, '{}')

    # <<< TRUSTEE cases >>>
    # Default Trustee adds Trustee1
    res = await send_nym(pool_handler, wallet_handler, trustee_did, trustee1_did, trustee1_vk, None, 'TRUSTEE')
    assert res['op'] == 'REPLY'
    # Trustee1 adds Steward1
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, steward1_did, steward1_vk, None, 'STEWARD')
    assert res['op'] == 'REPLY'
    # Trustee1 adds TrustAnchor1
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, anchor1_did, anchor1_vk, None, 'TRUST_ANCHOR')
    assert res['op'] == 'REPLY'
    # Trustee1 adds IdentityOwner1
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, identity1_did, identity1_vk, None, None)
    assert res['op'] == 'REPLY'
    # Steward1 tries to demote Trustee1 - should fail
    res = await send_nym(pool_handler, wallet_handler, steward1_did, trustee1_did, None, None, '')
    assert res['op'] == 'REJECT'
    # Default Trustee demotes Trustee1
    res = await send_nym(pool_handler, wallet_handler, trustee_did, trustee1_did, None, None, '')
    assert res['op'] == 'REPLY'
    # Trustee1 tries to add Steward2 after demotion - should fail
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, steward2_did, steward2_vk, None, 'STEWARD')
    assert res['op'] == 'REJECT'
    # Trustee1 tries to demote Steward1 after demotion - should fail
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, steward1_did, None, None, '')
    assert res['op'] == 'REJECT'
    # Default Trustee promotes Trustee1 back
    res = await send_nym(pool_handler, wallet_handler, trustee_did, trustee1_did, None, None, 'TRUSTEE')
    assert res['op'] == 'REPLY'
    # Trustee1 adds Steward2 after promotion
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, steward2_did, steward2_vk, None, 'STEWARD')
    assert res['op'] == 'REPLY'

    # <<< STEWARD cases >>>
    # Steward1 adds TrustAnchor2
    res = await send_nym(pool_handler, wallet_handler, steward1_did, anchor2_did, anchor2_vk, None, 'TRUST_ANCHOR')
    assert res['op'] == 'REPLY'
    # Steward1 adds IdentityOwner2
    res = await send_nym(pool_handler, wallet_handler, steward1_did, identity2_did, identity2_vk, None, None)
    assert res['op'] == 'REPLY'
    # TrustAnchor1 tries to demote Steward1 - should fail
    res = await send_nym(pool_handler, wallet_handler, anchor1_did, steward1_did, None, None, '')
    assert res['op'] == 'REJECT'
    # Trustee1 demotes Steward1
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, steward1_did, None, None, '')
    assert res['op'] == 'REPLY'
    # Steward1 tries to add TrustAnchor3 after demotion - should fail
    res = await send_nym(pool_handler, wallet_handler, steward1_did, anchor3_did, anchor3_vk, None, 'TRUST_ANCHOR')
    assert res['op'] == 'REJECT'
    # Steward1 tries to demote TrustAnchor2 after demotion - should fail
    res = await send_nym(pool_handler, wallet_handler, steward1_did, anchor2_did, None, None, '')
    assert res['op'] == 'REJECT'
    # Trustee1 promotes Steward1 back
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, steward1_did, None, None, 'STEWARD')
    assert res['op'] == 'REPLY'
    # Steward1 adds TrustAnchor3 after promotion
    res = await send_nym(pool_handler, wallet_handler, steward1_did, anchor3_did, anchor3_vk, None, 'TRUST_ANCHOR')
    assert res['op'] == 'REPLY'

    # <<< TRUST_ANCHOR cases >>>
    # TrustAnchor1 adds IdentityOwner3
    res = await send_nym(pool_handler, wallet_handler, anchor1_did, identity3_did, identity3_vk, None, None)
    assert res['op'] == 'REPLY'
    # IdentityOwner1 tries to demote TrustAnchor1 - should fail
    res = await send_nym(pool_handler, wallet_handler, identity1_did, anchor1_did, None, None, '')
    assert res['op'] == 'REJECT'
    # Trustee1 demotes TrustAnchor1
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, anchor1_did, None, None, '')
    assert res['op'] == 'REPLY'
    # TrustAnchor1 tries to add IdentityOwner4 after demotion - should fail
    res = await send_nym(pool_handler, wallet_handler, anchor1_did, identity4_did, identity4_vk, None, None)
    assert res['op'] == 'REJECT'
    # Trustee1 promotes TrustAnchor1 back
    res = await send_nym(pool_handler, wallet_handler, trustee1_did, anchor1_did, None, None, 'TRUST_ANCHOR')
    assert res['op'] == 'REPLY'
    # TrustAnchor1 adds IdentityOwner4 after promotion
    res = await send_nym(pool_handler, wallet_handler, anchor1_did, identity4_did, identity4_vk, None, None)
    assert res['op'] == 'REPLY'
