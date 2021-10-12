import pytest
import json
import hashlib
import time
import logging
import asyncio
from async_generator import async_generator, yield_

from indy import pool, did, ledger, IndyError

from system.utils import *

# logger = logging.getLogger(__name__)
# logging.basicConfig(level=0, format='%(asctime)s %(message)s')


@pytest.fixture
async def nodes_num():
    return 7


@pytest.fixture(scope='module', autouse=True)
@async_generator
async def docker_setup_and_teardown(docker_setup_and_teardown_module):
    await yield_()


@pytest.mark.parametrize('writer_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
@pytest.mark.parametrize('reader_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', None])
@pytest.mark.asyncio
async def test_send_and_get_nym_positive(writer_role, reader_role):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    target_did, target_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    writer_did, writer_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    reader_did, reader_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    # Trustee adds NYM writer
    await send_nym(pool_handle, wallet_handle, trustee_did, writer_did, writer_vk, None, writer_role)
    # Trustee adds NYM reader
    await send_nym(pool_handle, wallet_handle, trustee_did, reader_did, reader_vk, None, reader_role)
    # Writer sends NYM
    res1 = await send_nym(pool_handle, wallet_handle, writer_did, target_did)
    # Reader gets NYM
    res2 = await read_eventually_positive(get_nym, pool_handle, wallet_handle, target_did, target_did)

    assert res1['op'] == 'REPLY'
    assert res2['result']['seqNo'] is not None

    print(res1)
    print(res2)


@pytest.mark.parametrize('submitter_seed', ['{}',
                                            random_did_and_json()[1],
                                            random_seed_and_json()[1],
                                            ])
@pytest.mark.asyncio
async def test_send_and_get_nym_negative(submitter_seed):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    target_did, target_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    submitter_did, submitter_vk = await did.create_and_store_my_did(wallet_handle, submitter_seed)
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    # Trustee adds submitter
    await send_nym(pool_handle, wallet_handle, trustee_did, submitter_did, submitter_vk)
    # None role submitter tries to send NYM (rejected) and gets no data about this NYM from ledger
    res1 = await send_nym(pool_handle, wallet_handle, submitter_did, target_did)
    res2 = await get_nym(pool_handle, wallet_handle, submitter_did, target_did)

    assert res1['op'] == 'REJECT'
    assert res2['result']['seqNo'] is None

    print(res1)
    print(res2)


@pytest.mark.parametrize('xhash, raw, enc, raw_key', [
    (hashlib.sha256().hexdigest(), None, None, None),
    (None, json.dumps({'key': 'value'}), None, 'key'),
    (None, None, 'ENCRYPTED_STRING', None)
])
@pytest.mark.asyncio
async def test_send_and_get_attrib_positive(xhash, raw, enc, raw_key):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    target_did, target_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    submitter_did, submitter_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    await send_nym(pool_handle, wallet_handle, submitter_did, target_did, target_vk)
    # Writer sends ATTRIB
    res1 = await send_attrib(pool_handle, wallet_handle, target_did, target_did, xhash, raw, enc)
    # Reader gets ATTRIB
    res2 = await read_eventually_positive(
        get_attrib, pool_handle, wallet_handle, target_did, target_did, xhash, raw_key, enc
    )

    assert res1['op'] == 'REPLY'
    assert res2['result']['seqNo'] is not None

    print(res1)
    print(res2)


@pytest.mark.parametrize('xhash, raw, enc, error, readonly', [
    (None, None, None, IndyError, False),
    (hashlib.sha256().hexdigest(), json.dumps({'key': 'value'}), None, None, False),
    (None, json.dumps({'key': 'value'}), 'ENCRYPTED_STRING', None, False),
    (hashlib.sha256().hexdigest(), None, 'ENCRYPTED_STRING', None, False),
    (hashlib.sha256().hexdigest(), json.dumps({'key': 'value'}), 'ENCRYPTED_STRING', None, False),
    (hashlib.sha256().hexdigest(), None, None, None, True),
    (None, json.dumps({'key': 'value'}), None, None, True),
    (None, None, 'ENCRYPTED_STRING', None, True)
])
@pytest.mark.asyncio
async def test_send_and_get_attrib_negative(xhash, raw, enc, error, readonly):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    target_did, target_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    submitter_did, submitter_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    await send_nym(pool_handle, wallet_handle, submitter_did, target_did, target_vk)
    if error:
        with pytest.raises(error):
            await send_attrib(pool_handle, wallet_handle, target_did, target_did, xhash, raw, enc)
        with pytest.raises(error):
            await get_attrib(pool_handle, wallet_handle, target_did, target_did, xhash, raw, enc)
    elif readonly:
        res = await get_attrib(pool_handle, wallet_handle, target_did, target_did, xhash, raw, enc)
        assert res['result']['seqNo'] is None
        print(res)
    else:
        res1 = await send_attrib(pool_handle, wallet_handle, target_did, target_did, xhash, raw, enc)
        res2 = await get_attrib(pool_handle, wallet_handle, target_did, target_did, xhash, raw, enc)
        assert res1['op'] == 'REQNACK'
        assert res2['op'] == 'REQNACK'
        print(res1)
        print(res2)


@pytest.mark.parametrize('writer_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
@pytest.mark.parametrize('reader_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', None])
@pytest.mark.asyncio
async def test_send_and_get_schema_positive(writer_role, reader_role):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    writer_did, writer_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    reader_did, reader_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    # Trustee adds SCHEMA writer
    await send_nym(pool_handle, wallet_handle, trustee_did, writer_did, writer_vk, None, writer_role)
    # Trustee adds SCHEMA reader
    await send_nym(pool_handle, wallet_handle, trustee_did, reader_did, reader_vk, None, reader_role)
    # Writer sends SCHEMA
    schema_id, res1 = await send_schema(pool_handle, wallet_handle, writer_did,
                                        'schema1', '1.0', json.dumps(["age", "sex", "height", "name"]))
    # Reader gets SCHEMA
    res2 = await read_eventually_positive(
        get_schema, pool_handle, wallet_handle, reader_did, schema_id
    )

    assert res1['op'] == 'REPLY'
    assert res2['result']['seqNo'] is not None

    print(res1)
    print(res2)


@pytest.mark.parametrize('schema_name, schema_version, schema_attrs, schema_id, errors, readonly', [
    (None, None, None, None, (AttributeError, AttributeError), False),
    ('', '', '', '', (IndyError, IndyError), False),
    (1, 2, 3, 4, (AttributeError, AttributeError), False),
    (None, None, None, 'P2rRdR8q9aXiteCMJGvVkZ:2:schema:1.0', None, True)
])
@pytest.mark.asyncio
async def test_send_and_get_schema_negative(schema_name, schema_version, schema_attrs, schema_id, errors, readonly):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    if errors:
        with pytest.raises(errors[0]):
            await send_schema(pool_handle, wallet_handle, trustee_did, schema_name, schema_version, schema_attrs)
        with pytest.raises(errors[1]):
            await get_schema(pool_handle, wallet_handle, trustee_did, schema_id)
    elif readonly:
        res = await get_schema(pool_handle, wallet_handle, trustee_did, schema_id)
        assert res['result']['seqNo'] is None
        print(res)
    # TODO: get reqnacks from pool
    else:
        res1 = await send_schema(pool_handle, wallet_handle, trustee_did, schema_name, schema_version, schema_attrs)
        res2 = await get_schema(pool_handle, wallet_handle, trustee_did, schema_id)

        assert res1['op'] == 'REQNACK'
        assert res2['op'] == 'REQNACK'

        print(res1)
        print(res2)


@pytest.mark.parametrize('writer_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
@pytest.mark.parametrize('reader_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', None])
@pytest.mark.asyncio
async def test_send_and_get_cred_def_positive(writer_role, reader_role):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    writer_did, writer_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    reader_did, reader_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    # Trustee adds CRED_DEF writer
    await send_nym(pool_handle, wallet_handle, trustee_did, writer_did, writer_vk, None, writer_role)
    # Trustee adds CRED_DEF reader
    await send_nym(pool_handle, wallet_handle, trustee_did, reader_did, reader_vk, None, reader_role)
    schema_id, _ = await send_schema(pool_handle, wallet_handle, writer_did,
                                     'schema1', '1.0', json.dumps(["age", "sex", "height", "name"]))
    await asyncio.sleep(1)
    res = await get_schema(pool_handle, wallet_handle, reader_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, _, res1 = await send_cred_def(pool_handle, wallet_handle, writer_did, schema_json, 'TAG',
                                               None, json.dumps({'support_revocation': False}))
    res2 = await read_eventually_positive(
        get_cred_def, pool_handle, wallet_handle, reader_did, cred_def_id
    )

    assert res1['op'] == 'REPLY'
    assert res2['result']['seqNo'] is not None

    print(res1)
    print(res2)
    print(cred_def_id)


@pytest.mark.parametrize('schema_json, tag, signature_type, config_json, cred_def_id, errors, readonly', [
    (None, None, None, None, None, (AttributeError, AttributeError), False),
    ('', '', '', '', '', (IndyError, IndyError), False),
    (None, None, None, None, 'WL6zBSjE1RsttXSqLh8GtG:3:CL:999:tag', None, True)
])
@pytest.mark.asyncio
async def test_send_and_get_cred_def_negative(schema_json, tag, signature_type, config_json, cred_def_id, errors,
                                              readonly):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    if errors:
        with pytest.raises(errors[0]):
            await send_cred_def(
                pool_handle, wallet_handle, trustee_did, schema_json, tag, signature_type, config_json)
        with pytest.raises(errors[1]):
            await get_cred_def(pool_handle, wallet_handle, trustee_did, cred_def_id)
    elif readonly:
        res = await get_cred_def(pool_handle, wallet_handle, trustee_did, cred_def_id)
        assert res['result']['seqNo'] is None
        print(res)
    # TODO: get reqnacks from pool
    else:
        res1 = await send_cred_def(pool_handle, wallet_handle, trustee_did, schema_json, tag, signature_type,
                                   config_json)
        res2 = await get_cred_def(pool_handle, wallet_handle, trustee_did, cred_def_id)

        assert res1['op'] == 'REQNACK'
        assert res2['op'] == 'REQNACK'

        print(res1)
        print(res2)


@pytest.mark.parametrize('writer_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
@pytest.mark.parametrize('reader_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', None])
@pytest.mark.asyncio
async def test_send_and_get_revoc_reg_def_positive(writer_role, reader_role):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    writer_did, writer_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    reader_did, reader_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    # Trustee adds REVOC_REG_DEF writer
    await send_nym(pool_handle, wallet_handle, trustee_did, writer_did, writer_vk, None, writer_role)
    # Trustee adds REVOC_REG_DEF reader
    await send_nym(pool_handle, wallet_handle, trustee_did, reader_did, reader_vk, None, reader_role)
    schema_id, _ = await send_schema(pool_handle, wallet_handle, writer_did,
                                     'schema1', '1.0', json.dumps(['age', 'sex', 'height', 'name']))
    await asyncio.sleep(1)
    res = await get_schema(pool_handle, wallet_handle, reader_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, _, res = await send_cred_def(pool_handle, wallet_handle, writer_did, schema_json, 'cred_def_tag',
                                              None, json.dumps({'support_revocation': True}))
    revoc_reg_def_id, _, _, res1 = await send_revoc_reg_def(pool_handle, wallet_handle, writer_did, None,
                                                            'revoc_def_tag', cred_def_id,
                                                            json.dumps({'max_cred_num': 1,
                                                                        'issuance_type': 'ISSUANCE_BY_DEFAULT'}))
    res2 = await read_eventually_positive(
        get_revoc_reg_def, pool_handle, wallet_handle, reader_did, revoc_reg_def_id
    )

    assert res1['op'] == 'REPLY'
    assert res2['result']['seqNo'] is not None

    print(res1)
    print(res2)


@pytest.mark.asyncio
async def test_send_and_get_revoc_reg_def_negative():
    pass


@pytest.mark.parametrize('writer_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
@pytest.mark.parametrize('reader_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', None])
@pytest.mark.asyncio
async def test_send_and_get_revoc_reg_entry_positive(writer_role, reader_role):
    await pool.set_protocol_version(2)
    pool_handle, _ = await pool_helper()
    wallet_handle, _, _ = await wallet_helper()
    writer_did, writer_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    reader_did, reader_vk = await did.create_and_store_my_did(wallet_handle, '{}')
    trustee_did, trustee_vk = await did.create_and_store_my_did(wallet_handle, json.dumps(
        {'seed': '000000000000000000000000Trustee1'}))
    timestamp0 = int(time.time())
    # Trustee adds REVOC_REG_ENTRY writer
    await send_nym(pool_handle, wallet_handle, trustee_did, writer_did, writer_vk, None, writer_role)
    # Trustee adds REVOC_REG_ENTRY reader
    await send_nym(pool_handle, wallet_handle, trustee_did, reader_did, reader_vk, None, reader_role)
    schema_id, _ = await send_schema(pool_handle, wallet_handle, writer_did,
                                     'schema1', '1.0', json.dumps(['age', 'sex', 'height', 'name']))
    await asyncio.sleep(1)
    res = await get_schema(pool_handle, wallet_handle, reader_did, schema_id)
    schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
    cred_def_id, _, res = await send_cred_def(pool_handle, wallet_handle, writer_did, schema_json, 'cred_def_tag',
                                              'CL', json.dumps({'support_revocation': True}))
    revoc_reg_def_id, _, _, res1 = await send_revoc_reg_entry(pool_handle, wallet_handle, writer_did, 'CL_ACCUM',
                                                              'revoc_def_tag', cred_def_id,
                                                              json.dumps({'max_cred_num': 1,
                                                                          'issuance_type': 'ISSUANCE_BY_DEFAULT'}))
    timestamp1 = int(time.time())

    res2 = await read_eventually_positive(
        get_revoc_reg, pool_handle, wallet_handle, reader_did, revoc_reg_def_id, timestamp1
    )

    res3 = await read_eventually_positive(
        get_revoc_reg_delta, pool_handle, wallet_handle, reader_did, revoc_reg_def_id, timestamp0, timestamp1
    )

    assert res1['op'] == 'REPLY'
    assert res2['result']['seqNo'] is not None
    assert res3['result']['seqNo'] is not None

    print(res1)
    print(res2)
    print(res3)


@pytest.mark.asyncio
async def test_send_and_get_revoc_reg_entry_negative():
    pass
