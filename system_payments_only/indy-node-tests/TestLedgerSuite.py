import pytest
import asyncio
from system_payments_only.utils import *
from async_generator import async_generator, yield_


# setup once for all cases
@pytest.fixture(scope='module', autouse=True)
@async_generator
async def docker_setup_and_teardown(docker_setup_and_teardown_module):
    await yield_()


# TODO IMPLEMENT AND PARAMETRIZE ALL POSITIVE AND NEGATIVE CASES
@pytest.mark.usefixtures('check_no_failures_fixture')
class TestLedgerSuite:

    @pytest.mark.parametrize('ledger_type', ['DOMAIN', 'POOL', 'CONFIG', '1001'])
    @pytest.mark.parametrize('seqno', [1, 5])
    @pytest.mark.asyncio
    # 						    GET_TXN
    async def test_get_txn(
            self, pool_handler, wallet_handler, get_default_trustee, initial_token_minting, initial_fees_setting,
            payment_init, ledger_type, seqno
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        initial_token_minting
        initial_fees_setting
        # --------------------------------------------------------------------------------------------------------------
        req = await ledger.build_get_txn_request(trustee_did, ledger_type, seqno)
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        assert res['result']['seqNo'] is not None