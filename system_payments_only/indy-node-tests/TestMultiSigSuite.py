import pytest
import asyncio
from system_payments_only.utils import *
from indy import payment


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestMultiSigSuite:

    @pytest.mark.asyncio
    async def test_case_double_mint(self, payment_init, pool_handler, wallet_handler, get_default_trustee):
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        trustee_did4, trustee_vk4 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee4')}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, 'Trustee 2', 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, 'Trustee 3', 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did4, trustee_vk4, 'Trustee 4', 'TRUSTEE')
        address = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps(
            {"seed": str('0000000000000000000000000Wallet0')}))
        output = {"recipient": address, "amount": 1000}
        req, _ = await payment.build_mint_req(wallet_handler, trustee_did, json.dumps([output]), random_string(10))
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)

        res1 = json.loads(await ledger.submit_request(pool_handler, req))
        print('\n{}'.format(res1))
        assert res1['op'] == 'REPLY'
        await asyncio.sleep(5)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did4, req)
        res2 = json.loads(await ledger.submit_request(pool_handler, req))
        print('\n{}'.format(res2))
        assert res2['op'] == 'REQNACK'