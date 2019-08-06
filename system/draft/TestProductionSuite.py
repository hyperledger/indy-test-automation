import pytest
import asyncio
from system.utils import *

import logging
logger = logging.getLogger(__name__)


class TestProductionSuite:

    @pytest.mark.asyncio
    async def test_case_complex_pool_creation(
            self, pool_handler, wallet_handler, get_default_trustee
    ):
        pass
