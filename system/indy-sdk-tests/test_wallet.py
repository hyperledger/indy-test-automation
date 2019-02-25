import time
import pytest
from system.utils import *
from indy import wallet, IndyError
import os


@pytest.mark.parametrize('wallet_config, wallet_credentials', [
    (json.dumps({'id': random_string(10)}),
     json.dumps({"key": ''})),
    (json.dumps({'id': random_string(1)}),
     json.dumps({'key': random_string(100), 'key_derivation_method': 'ARGON2I_MOD'})),
    (json.dumps({'id': random_string(100)}),
     json.dumps({'key': random_string(1), 'key_derivation_method': 'ARGON2I_INT'}))
])
@pytest.mark.asyncio
async def test_wallet_create_open_positive(wallet_config, wallet_credentials):
    res1 = await wallet.create_wallet(wallet_config, wallet_credentials)
    res2 = await wallet.open_wallet(wallet_config, wallet_credentials)

    assert res1 is None
    assert isinstance(res2, int)


@pytest.mark.asyncio
async def test_wallet_close_delete_positive():
    wallet_handle, wallet_config, wallet_credentials = await wallet_helper()
    res1 = await wallet.close_wallet(wallet_handle)
    res2 = await wallet.delete_wallet(wallet_config, wallet_credentials)

    assert res1 is None
    assert res2 is None


@pytest.mark.parametrize('exp_config, imp_config', [
    (json.dumps({'path': './wallet', 'key': 'abc'}),
     json.dumps({'path': './wallet', 'key': 'abc'})),
    (json.dumps({'path': './wallet', 'key': 'bac', 'key_derivation_method': 'ARGON2I_MOD'}),
     json.dumps({'path': './wallet', 'key': 'bac', 'key_derivation_method': 'ARGON2I_INT'})),
    (json.dumps({'path': './wallet', 'key': 'bca', 'key_derivation_method': 'ARGON2I_INT'}),
     json.dumps({'path': './wallet', 'key': 'bca', 'key_derivation_method': 'ARGON2I_MOD'}))
])
@pytest.mark.asyncio
async def test_wallet_export_import_positive(exp_config, imp_config):
    wallet_handle, wallet_config, wallet_credentials = await wallet_helper()
    res1 = await wallet.export_wallet(wallet_handle, exp_config)
    await wallet_destructor(wallet_handle, wallet_config, wallet_credentials)
    res2 = await wallet.import_wallet(wallet_config, wallet_credentials, imp_config)
    os.remove('./wallet')

    assert res1 is None
    assert res2 is None


@pytest.mark.parametrize('config', [None,
                                    json.dumps({'seed': '0000000000000000000000000000seed'}),
                                    json.dumps({'seed': random_string(32)})])
@pytest.mark.asyncio
async def test_generate_wallet_key_positive(config):
    res = await wallet.generate_wallet_key(config)
    print(res)
# ---------------------


@pytest.mark.parametrize('wallet_config, wallet_credentials, exceptions', [
    (None, None, (AttributeError, AttributeError)),
    (json.dumps({"id": ''}), json.dumps({"key": 1}), (IndyError, IndyError))
])
@pytest.mark.asyncio
async def test_wallet_create_open_negative(wallet_config, wallet_credentials, exceptions):
    with pytest.raises(exceptions[0]):
        await wallet.create_wallet(wallet_config, wallet_credentials)
    with pytest.raises(exceptions[1]):
        await wallet.open_wallet(wallet_config, wallet_credentials)


@pytest.mark.parametrize('wallet_handle', [-99, 0, 99])
@pytest.mark.parametrize('wallet_config, wallet_credentials, exceptions', [
    (None, None, (AttributeError,)),
    (json.dumps({"id": ''}), json.dumps({"key": 1}), (IndyError,))
])
@pytest.mark.asyncio
async def test_wallet_close_delete_negative(wallet_handle, wallet_config, wallet_credentials, exceptions):
    with pytest.raises(IndyError):
        await wallet.close_wallet(wallet_handle)
    with pytest.raises(exceptions[0]):
        await wallet.delete_wallet(wallet_config, wallet_credentials)


@pytest.mark.parametrize('wallet_handle, exp_config, exceptions_e', [
    (None, None, (AttributeError,))
])
@pytest.mark.parametrize('wallet_config, wallet_credentials, imp_config, exceptions_i', [
    (None, None, None, (AttributeError,))
])
@pytest.mark.asyncio
async def test_wallet_export_import_negative(wallet_handle, wallet_config, wallet_credentials, exp_config, imp_config,
                                             exceptions_e, exceptions_i):
    with pytest.raises(exceptions_e[0]):
        await wallet.export_wallet(wallet_handle, exp_config)
    with pytest.raises(exceptions_i[0]):
        await wallet.import_wallet(wallet_config, wallet_credentials, imp_config)


@pytest.mark.parametrize('config', [json.dumps({'seed': ''}), json.dumps({'seed': random_string(1)}),
                                    json.dumps({'seed': random_string(33)})])
@pytest.mark.asyncio
async def test_generate_wallet_key_negative(config):
    with pytest.raises(IndyError):
        await wallet.generate_wallet_key(config)
# ---------------------


@pytest.mark.asyncio
async def test_key_derivation_algorithm():
    await pool.set_protocol_version(2)
    config_mod = json.dumps({"id": ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))})
    credentials_mod = json.dumps({"key": '', "key_derivation_method": 'ARGON2I_MOD'})
    t1_start = float(time.time())
    await wallet.create_wallet(config_mod, credentials_mod)
    t1_create_delta = float(time.time()) - t1_start
    handle_mod = await wallet.open_wallet(config_mod, credentials_mod)
    t1_open_delta = float(time.time()) - t1_start - t1_create_delta
    await wallet.close_wallet(handle_mod)
    t1_close_delta = float(time.time()) - t1_start - t1_create_delta - t1_open_delta
    await wallet.delete_wallet(config_mod, credentials_mod)
    t1_delete_delta = float(time.time()) - t1_start - t1_create_delta - t1_open_delta - t1_close_delta
    print('\n', t1_create_delta, '\n', t1_open_delta, '\n', t1_close_delta, '\n', t1_delete_delta)

    config_int = json.dumps({"id": ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))})
    credentials_int = json.dumps({"key": '', "key_derivation_method": 'ARGON2I_INT'})
    t2_start = float(time.time())
    await wallet.create_wallet(config_int, credentials_int)
    t2_create_delta = float(time.time()) - t2_start
    handle_int = await wallet.open_wallet(config_int, credentials_int)
    t2_open_delta = float(time.time()) - t2_start - t2_create_delta
    await wallet.close_wallet(handle_int)
    t2_close_delta = float(time.time()) - t2_start - t2_create_delta - t2_open_delta
    await wallet.delete_wallet(config_int, credentials_int)
    t2_delete_delta = float(time.time()) - t2_start - t2_create_delta - t2_open_delta - t2_close_delta
    print('\n', t2_create_delta, '\n', t2_open_delta, '\n', t2_close_delta, '\n', t2_delete_delta)

    assert(t2_create_delta < t1_create_delta)
    assert(t2_open_delta < t1_open_delta)
    assert(t2_delete_delta < t1_delete_delta)
