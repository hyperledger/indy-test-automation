import pytest
from system.utils import *
from indy import payment
from hypothesis import settings, given, strategies

max_size = 1e+17


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestTokensSuiteProp:

    @settings(deadline=None, max_examples=250)
    @given(amount=strategies.integers(min_value=1, max_value=max_size))
    @pytest.mark.asyncio
    async def test_token_minting_positive(
            self, payment_init, pool_handler, wallet_handler, get_default_trustee, amount
    ):
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        try:
            trustee_did2, trustee_vk2 = await did.create_and_store_my_did(
                wallet_handler, json.dumps({"seed": str('000000000000000000000000Trustee2')})
            )
            trustee_did3, trustee_vk3 = await did.create_and_store_my_did(
                wallet_handler, json.dumps({"seed": str('000000000000000000000000Trustee3')})
            )
            await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
            await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
        except IndyError:
            trustee_did2, trustee_vk2 = 'LnXR1rPnncTPZvRdmJKhJQ', 'BnSWTUQmdYCewSGFrRUhT6LmKdcCcSzRGqWXMPnEP168'
            trustee_did3, trustee_vk3 = 'PNQm3CwyXbN5e39Rw3dXYx', 'DC8gEkb1cb4T9n3FcZghTkSp1cGJaZjhsPdxitcu6LUj'
        address = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps({}))
        req = json.dumps(
            {
                "operation":
                    {
                        "type": "10000",
                        "outputs": [
                            {
                                "address": address.split(':')[-1],
                                "amount": amount
                            }
                        ]
                    },
                "reqId": int(time.time()),
                "protocolVersion": 2,
                "identifier": "V4SGRU86Z58d6TV7PBUe6f"
            }
        )
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
        res = json.loads(await ledger.submit_request(pool_handler, req))
        print(res)
        assert res['op'] == 'REPLY'

    @settings(deadline=None, max_examples=250)
    @given(
        amount=
        strategies.integers(min_value=-max_size, max_value=0)
        | strategies.floats(min_value=-max_size, max_value=max_size, allow_nan=False, allow_infinity=False)
        | strategies.text(min_size=1, max_size=max_size)
    )
    @pytest.mark.asyncio
    async def test_token_minting_negative(
            self, payment_init, pool_handler, wallet_handler, get_default_trustee, amount
    ):
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        try:
            trustee_did2, trustee_vk2 = await did.create_and_store_my_did(
                wallet_handler, json.dumps({"seed": str('000000000000000000000000Trustee2')})
            )
            trustee_did3, trustee_vk3 = await did.create_and_store_my_did(
                wallet_handler, json.dumps({"seed": str('000000000000000000000000Trustee3')})
            )
            await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
            await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
        except IndyError:
            trustee_did2, trustee_vk2 = 'LnXR1rPnncTPZvRdmJKhJQ', 'BnSWTUQmdYCewSGFrRUhT6LmKdcCcSzRGqWXMPnEP168'
            trustee_did3, trustee_vk3 = 'PNQm3CwyXbN5e39Rw3dXYx', 'DC8gEkb1cb4T9n3FcZghTkSp1cGJaZjhsPdxitcu6LUj'
        address = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps({}))
        req = json.dumps(
            {
                "operation":
                    {
                        "type": "10000",
                        "outputs": [
                            {
                                "address": address.split(':')[-1],
                                "amount": amount
                            }
                        ]
                    },
                "reqId": int(time.time()),
                "protocolVersion": 2,
                "identifier": "V4SGRU86Z58d6TV7PBUe6f"
            }
        )
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
        res = json.loads(await ledger.submit_request(pool_handler, req))
        print(res)
        assert res['op'] == 'REQNACK'
