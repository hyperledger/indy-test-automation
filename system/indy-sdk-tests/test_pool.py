import pytest
from system.utils import *
from indy import IndyError


@pytest.mark.parametrize('pool_name, pool_config', [
    (random_string(1), json.dumps({'genesis_txn': '../stn_genesis'})),
    (random_string(100), json.dumps({'genesis_txn': '../docker_genesis'}))
])
@pytest.mark.asyncio
async def test_pool_create_open_refresh_positive(pool_name, pool_config):
    await pool.set_protocol_version(2)
    res1 = await pool.create_pool_ledger_config(pool_name, pool_config)
    res2 = await pool.open_pool_ledger(pool_name, pool_config)
    res3 = await pool.refresh_pool_ledger(res2)
    await pool_destructor(res2, pool_name)

    assert res1 is None
    assert isinstance(res2, int)
    assert res3 is None


@pytest.mark.asyncio
async def test_pool_close_delete_positive():
    await pool.set_protocol_version(2)
    pool_handle, pool_name = await pool_helper()
    res1 = await pool.close_pool_ledger(pool_handle)
    res2 = await pool.delete_pool_ledger_config(pool_name)

    assert res1 is None
    assert res2 is None
# ---------------------


@pytest.mark.parametrize('pool_name, pool_config, pool_handle, exceptions', [
    (None, json.dumps({'genesis_txn': '../stn_genesis'}), 99, (AttributeError, AttributeError, IndyError)),
    (random_string(10), None, -99, (IndyError, IndyError, IndyError))
])
@pytest.mark.asyncio
async def test_pool_create_open_refresh_negative(pool_name, pool_config, pool_handle, exceptions):
    await pool.set_protocol_version(2)
    with pytest.raises(exceptions[0]):
        await pool.create_pool_ledger_config(pool_name, pool_config)
    with pytest.raises(exceptions[1]):
        await pool.open_pool_ledger(pool_name, pool_config)
    with pytest.raises(exceptions[2]):
        await pool.refresh_pool_ledger(pool_handle)


@pytest.mark.parametrize('pool_handle', [-99, 0, 99])
@pytest.mark.parametrize('pool_name', [random_string(10), ''])
@pytest.mark.asyncio
async def test_pool_close_delete_negative(pool_handle, pool_name):
    await pool.set_protocol_version(2)
    with pytest.raises(IndyError):
        await pool.close_pool_ledger(pool_handle)
    with pytest.raises(IndyError):
        await pool.delete_pool_ledger_config(pool_name)
