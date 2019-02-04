import pytest
import time
import logging

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=0, format='%(asctime)s %(message)s')


@pytest.mark.asyncio
async def test_vc_by_restart(pool_handler, wallet_handler, get_default_trustee, send_and_get_nyms_before_and_after,
                             stop_and_start_primary):
    time.sleep(240)


@pytest.mark.asyncio
async def test_vc_by_demotion(pool_handler, wallet_handler, get_default_trustee, send_and_get_nyms_before_and_after,
                              demote_and_promote_primary):
    time.sleep(240)
