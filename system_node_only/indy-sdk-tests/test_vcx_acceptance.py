import pytest
import json
import time
import os
import asyncio
from system.utils import payment_initializer
from vcx.api.vcx_init import vcx_init_with_config
from vcx.api.utils import vcx_agent_provision
from vcx.api.wallet import Wallet
from vcx.common import mint_tokens, shutdown
from vcx.error import VcxError

# import logging
# logging.basicConfig(level=0)
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger().setLevel(0)


@pytest.mark.asyncio
async def test_vcx_mint_token():
    try:
        library = 'libnullpay.so'
        initializer = 'nullpay_init'
        config = json.dumps(json.loads(open('./config.json').read()))
        await payment_initializer(library, initializer)
        os.system('cd /home/indy/indy-sdk/vcx/dummy-cloud-agent; cargo run config/sample-config.json &')
        await asyncio.sleep(180)
        """ Mint tokens to send """
        # Create the connection to before processing the credential
        await vcx_agent_provision(config)
        await vcx_init_with_config(config)
        # Mint tokens and store in wallet
        mint_tokens()  # three addresses and 1000 tokens each - puts stuff in wallet only...
        tkn = await Wallet.get_token_info(0)
        print("\nToken info before: %s " % tkn)
        address = await Wallet.create_payment_address()
        # Send tokens - test for EN-479
        rec = await Wallet.send_tokens(0, 50000000000, address.decode())
        rec = json.loads(rec.decode().strip())
        assert rec['op'] == 'REPLY'
        tkn2 = await Wallet.get_token_info(0)
        print("\nToken info after: %s " % tkn2)
        assert tkn != tkn2
        shutdown(True)
    except VcxError as ex:
        print('EXCEPTION HAS BEEN THROWN >>> {}'.format(ex))
    finally:
        os.system('killall -9 indy-dummy-agent')
