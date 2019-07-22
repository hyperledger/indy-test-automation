import time
from datetime import datetime
import os
import string
import base58
import asyncio
from random import sample, shuffle
from collections import Counter
from collections.abc import Iterable
from inspect import isawaitable
import random
import functools
from ctypes import CDLL
import testinfra
import json
from json import JSONDecodeError

from indy import pool, wallet, did, ledger, anoncreds, blob_storage, IndyError


import logging
logger = logging.getLogger(__name__)


MODULE_PATH = os.path.abspath(os.path.dirname(__file__))
POOL_GENESIS_PATH = os.path.join(MODULE_PATH, 'docker_genesis')


def run_async_method(method, *args, **kwargs):
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(method(*args, **kwargs))
    return result


def random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def random_did_and_json():
    return base58.b58encode(random_string(16)).decode(),\
        json.dumps({'did': base58.b58encode(random_string(16)).decode()})


def random_seed_and_json():
    return random_string(32), json.dumps({'seed': random_string(32)})


async def pool_helper(pool_name=None, path_to_genesis=POOL_GENESIS_PATH, node_list=None):
    if not pool_name:
        pool_name = random_string(25)
    if node_list:
        pool_config = json.dumps({"genesis_txn": path_to_genesis, "preordered_nodes": node_list})
    else:
        pool_config = json.dumps({"genesis_txn": path_to_genesis})
    # print(pool_config)
    await pool.create_pool_ledger_config(pool_name, pool_config)
    pool_handle = await pool.open_pool_ledger(pool_name, pool_config)

    return pool_handle, pool_name


async def wallet_helper(wallet_id=None, wallet_key='', wallet_key_derivation_method='ARGON2I_INT'):
    if not wallet_id:
        wallet_id = random_string(25)
    wallet_config = json.dumps({"id": wallet_id})
    wallet_credentials = json.dumps({"key": wallet_key, "key_derivation_method": wallet_key_derivation_method})
    await wallet.create_wallet(wallet_config, wallet_credentials)
    wallet_handle = await wallet.open_wallet(wallet_config, wallet_credentials)

    return wallet_handle, wallet_config, wallet_credentials


async def pool_destructor(pool_handle, pool_name):
    await pool.close_pool_ledger(pool_handle)
    await pool.delete_pool_ledger_config(pool_name)


async def wallet_destructor(wallet_handle, wallet_config, wallet_credentials):
    await wallet.close_wallet(wallet_handle)
    await wallet.delete_wallet(wallet_config, wallet_credentials)


async def default_trustee(wallet_handle):
    trustee_did, trustee_vk = await did.create_and_store_my_did(
        wallet_handle, json.dumps({'seed': '000000000000000000000000Trustee1'}))
    return trustee_did, trustee_vk


# TODO why we need that async ???
async def payment_initializer(library_name, initializer_name):
    library = CDLL(library_name)
    init = getattr(library, initializer_name)
    init()


async def eventually(awaited_func,
                     *args,
                     retry_wait: float = 1,
                     timeout: float = 15,
                     acceptableExceptions=None,
                     verbose=True,
                     **kwargs):
    if not timeout > 0:
        raise ValueError("'timeout' is {}".format(timeout))
    if acceptableExceptions and not isinstance(acceptableExceptions, Iterable):
        acceptableExceptions = [acceptableExceptions]

    start = time.perf_counter()

    fname = awaited_func.__name__
    while True:
        remain = 0
        try:
            remain = start + timeout - time.perf_counter()
            if remain < 0:
                # this provides a convenient breakpoint for a debugger
                logger.debug("{} last try...".format(fname))
            # noinspection PyCallingNonCallable
            res = awaited_func(*args, **kwargs)

            if isawaitable(res):
                result = await res
            else:
                result = res

            if verbose:
                logger.debug("{} succeeded with {:.2f} seconds to spare".
                             format(fname, remain))
            return result
        except Exception as ex:
            if acceptableExceptions and type(ex) not in acceptableExceptions:
                raise
            if remain >= 0:
                sleep_dur = retry_wait
                if verbose:
                    logger.debug("{} not succeeded yet, {:.2f} seconds "
                                 "remaining..., will sleep for {}".format(fname, remain, sleep_dur))
                await asyncio.sleep(sleep_dur)
            else:
                logger.error("{} failed; not trying any more because {} "
                             "seconds have passed; args were {}".
                             format(fname, timeout, args))
                raise ex


async def send_nym(pool_handle, wallet_handle, submitter_did, target_did,
                   target_vk=None, target_alias=None, target_role=None):
    req = await ledger.build_nym_request(submitter_did, target_did, target_vk, target_alias, target_role)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def send_attrib(pool_handle, wallet_handle, submitter_did, target_did, xhash=None, raw=None, enc=None):
    req = await ledger.build_attrib_request(submitter_did, target_did, xhash, raw, enc)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def send_schema(pool_handle, wallet_handle, submitter_did, schema_name, schema_version, schema_attrs):
    schema_id, schema_json = await anoncreds.issuer_create_schema(submitter_did, schema_name, schema_version,
                                                                  schema_attrs)
    req = await ledger.build_schema_request(submitter_did, schema_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return schema_id, res


async def send_cred_def(pool_handle, wallet_handle, submitter_did, schema_json, tag, signature_type, config_json):
    cred_def_id, cred_def_json = \
        await anoncreds.issuer_create_and_store_credential_def(wallet_handle, submitter_did, schema_json, tag,
                                                               signature_type, config_json)
    req = await ledger.build_cred_def_request(submitter_did, cred_def_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return cred_def_id, cred_def_json, res


async def send_revoc_reg_def(pool_handle, wallet_handle, submitter_did, revoc_def_type, tag, cred_def_id, config_json):
    tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
    tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
    revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = \
        await anoncreds.issuer_create_and_store_revoc_reg(wallet_handle, submitter_did, revoc_def_type, tag,
                                                          cred_def_id, config_json, tails_writer_handle)
    req = await ledger.build_revoc_reg_def_request(submitter_did, revoc_reg_def_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json, res


async def send_revoc_reg_entry(pool_handle, wallet_handle, submitter_did, revoc_def_type, tag, cred_def_id, config_json):
    tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
    tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
    revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = \
        await anoncreds.issuer_create_and_store_revoc_reg(wallet_handle, submitter_did, revoc_def_type, tag,
                                                          cred_def_id, config_json, tails_writer_handle)
    req = await ledger.build_revoc_reg_def_request(submitter_did, revoc_reg_def_json)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req)
    req = await ledger.build_revoc_reg_entry_request(submitter_did, revoc_reg_def_id, revoc_def_type,
                                                     revoc_reg_entry_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json, res


async def get_nym(pool_handle, wallet_handle, submitter_did, target_did):
    req = await ledger.build_get_nym_request(submitter_did, target_did)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_attrib(pool_handle, wallet_handle, submitter_did, target_did, xhash=None, raw=None, enc=None):
    req = await ledger.build_get_attrib_request(submitter_did, target_did, raw, xhash, enc)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_schema(pool_handle, wallet_handle, submitter_did, id_):
    req = await ledger.build_get_schema_request(submitter_did, id_)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_cred_def(pool_handle, wallet_handle, submitter_did, id_):
    req = await ledger.build_get_cred_def_request(submitter_did, id_)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_revoc_reg_def(pool_handle, wallet_handle, submitter_did, id_):
    req = await ledger.build_get_revoc_reg_def_request(submitter_did, id_)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_revoc_reg(pool_handle, wallet_handle, submitter_did, id_, timestamp):
    req = await ledger.build_get_revoc_reg_request(submitter_did, id_, timestamp)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_revoc_reg_delta(pool_handle, wallet_handle, submitter_did, id_, from_, to_):
    req = await ledger.build_get_revoc_reg_delta_request(submitter_did, id_, from_, to_)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


def run_in_event_loop(async_func):
    @functools.wraps(async_func)
    def wrapped(operations, queue_size, add_size, get_size, event_loop):
        event_loop.run_until_complete(asyncio.ensure_future(
            async_func(operations, queue_size, add_size, get_size, event_loop),
            loop=event_loop,
        ))
    return wrapped


async def send_and_get_nym(pool_handle, wallet_handle, trustee_did, some_did=None):
    if some_did is None:
        some_did, _ = await did.create_and_store_my_did(wallet_handle, '{}')
    add = await write_eventually_positive(send_nym, pool_handle, wallet_handle, trustee_did, some_did)
    assert add['op'] == 'REPLY'
    get = await read_eventually_positive(get_nym, pool_handle, wallet_handle, trustee_did, some_did)
    assert get['result']['seqNo'] is not None


# TODO make that async
def check_no_failures(hosts):
    for host in hosts:
        result = host.run('journalctl -u indy-node.service -b -p info')
        assert result.find("indy-node.service: Failed") == -1, (
            "Node service on host{} failed:\n{}".format(host.id, result)
        )


async def check_pool_performs_write(pool_handle, wallet_handle, submitter_did, nyms_count=1):
    res = []
    for _ in range(nyms_count):
        some_did, _ = await did.create_and_store_my_did(wallet_handle, '{}')
        resp = await send_nym(pool_handle, wallet_handle, submitter_did, some_did)
        assert resp['op'] == 'REPLY'
        res.append(resp)
    return res


async def check_pool_performs_read(pool_handle, wallet_handle, submitter_did, dids):
    res = []
    for did in dids:
        resp = await get_nym(pool_handle, wallet_handle, submitter_did, did)
        assert resp['result']['seqNo'] is not None
        res.append(resp)
    return res


async def check_pool_performs_write_read(
    pool_handle, wallet_handle, trustee_did, nyms_count=1
):
    writes = await check_pool_performs_write(
        pool_handle, wallet_handle, trustee_did, nyms_count=nyms_count
    )
    dids = [resp['result']['txn']['data']['dest'] for resp in writes]
    return await eventually(
        check_pool_performs_read, pool_handle, wallet_handle, trustee_did, dids
    )


async def ensure_pool_performs_write_read(
    pool_handle, wallet_handle, trustee_did, nyms_count=1, timeout=30
):
    await eventually(
        check_pool_performs_write_read, pool_handle, wallet_handle, trustee_did,
        nyms_count=nyms_count, timeout=timeout
    )


async def check_pool_is_functional(
    pool_handle, wallet_handle, trustee_did, nyms_count=3
):
    await check_pool_performs_write_read(
        pool_handle, wallet_handle, trustee_did, nyms_count=nyms_count
    )


async def ensure_pool_is_functional(
    pool_handle, wallet_handle, trustee_did, nyms_count=3, timeout=30
):
    await ensure_pool_performs_write_read(
        pool_handle, wallet_handle, trustee_did,
        nyms_count=nyms_count, timeout=timeout
    )


async def check_pool_is_in_sync(node_ids=None, nodes_num=7):
    if node_ids is None:
        node_ids = [(i + 1) for i in range(nodes_num)]
    hosts = [NodeHost(i) for i in node_ids]

    # TODO make that async
    pool_results = [host.run('read_ledger --type=pool --count') for host in hosts]
    print('\nPOOL LEDGER SYNC: {}'.format([result for result in pool_results]))
    config_results = [host.run('read_ledger --type=config --count') for host in hosts]
    print('\nCONFIG LEDGER SYNC: {}'.format([result for result in config_results]))
    domain_results = [host.run('read_ledger --type=domain --count') for host in hosts]
    print('\nDOMAIN LEDGER SYNC: {}'.format([result for result in domain_results]))
    audit_results = [host.run('read_ledger --type=audit --count') for host in hosts]
    print('\nAUDIT LEDGER SYNC: {}'.format([result for result in audit_results]))

    for res in (pool_results, config_results, domain_results, audit_results):
        assert len(set(res)) == 1


async def ensure_pool_is_in_sync(node_ids=None, nodes_num=7):
    await eventually(
        check_pool_is_in_sync, node_ids=node_ids, nodes_num=nodes_num,
        retry_wait=5, timeout=90
    )


async def check_primary_changed(pool_handler, wallet_handler, trustee_did, primary_before):
    primary_after, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
    assert primary_after != primary_before
    return primary_after


async def ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_before):
    return await eventually(
        check_primary_changed, pool_handler, wallet_handler, trustee_did, primary_before,
        retry_wait=10, timeout=480
    )


# TODO use threads to make that concurrent/async
def restart_pool(hosts):
    # restart all nodes using stop/start just to avoid
    # the case when some node is already restarted while
    # some others are still running
    for host in hosts:
        host.stop_service()
    for host in hosts:
        host.start_service()


async def stop_primary(pool_handle, wallet_handle, trustee_did):
    try:
        req = await ledger.build_get_validator_info_request(trustee_did)
        results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
        try:
            result = json.loads(sample(results.items(), 1)[0][1])
        except JSONDecodeError:
            try:
                shuffle(list(results.keys()))
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                shuffle(list(results.keys()))
                result = json.loads(sample(results.items(), 1)[0][1])
        name_before = result['result']['data']['Node_info']['Name']
        primary_before =\
            result['result']['data']['Node_info']['Replicas_status'][name_before+':0']['Primary'][len('Node'):
                                                                                                  -len(':0')]
    except TypeError:
        try:
            await asyncio.sleep(120)
            req = await ledger.build_get_validator_info_request(trustee_did)
            results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
            try:
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                try:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
                except JSONDecodeError:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
            name_before = result['result']['data']['Node_info']['Name']
            primary_before = \
                result['result']['data']['Node_info']['Replicas_status'][name_before + ':0']['Primary'][len('Node'):
                                                                                                        -len(':0')]
        except TypeError:
            await asyncio.sleep(240)
            req = await ledger.build_get_validator_info_request(trustee_did)
            results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
            try:
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                try:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
                except JSONDecodeError:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
            name_before = result['result']['data']['Node_info']['Name']
            primary_before = \
                result['result']['data']['Node_info']['Replicas_status'][name_before + ':0']['Primary'][len('Node'):
                                                                                                        -len(':0')]
    host = testinfra.get_host('docker://node'+primary_before)
    host.run('systemctl stop indy-node')
    print('\nPRIMARY NODE {} HAS BEEN STOPPED!'.format(primary_before))

    return primary_before


async def start_primary(pool_handle, wallet_handle, trustee_did, primary_before):
    host = testinfra.get_host('docker://node'+primary_before)
    host.run('systemctl start indy-node')
    try:
        req = await ledger.build_get_validator_info_request(trustee_did)
        results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
        try:
            result = json.loads(sample(results.items(), 1)[0][1])
        except JSONDecodeError:
            try:
                shuffle(list(results.keys()))
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                shuffle(list(results.keys()))
                result = json.loads(sample(results.items(), 1)[0][1])
        name_after = result['result']['data']['Node_info']['Name']
        primary_after =\
            result['result']['data']['Node_info']['Replicas_status'][name_after+':0']['Primary'][len('Node'):-len(':0')]
    except TypeError:
        try:
            await asyncio.sleep(120)
            req = await ledger.build_get_validator_info_request(trustee_did)
            results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
            try:
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                try:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
                except JSONDecodeError:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
            name_after = result['result']['data']['Node_info']['Name']
            primary_after = \
                result['result']['data']['Node_info']['Replicas_status'][name_after + ':0']['Primary'][len('Node'):
                                                                                                       -len(':0')]
        except TypeError:
            await asyncio.sleep(240)
            req = await ledger.build_get_validator_info_request(trustee_did)
            results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
            try:
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                try:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
                except JSONDecodeError:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
            name_after = result['result']['data']['Node_info']['Name']
            primary_after = \
                result['result']['data']['Node_info']['Replicas_status'][name_after + ':0']['Primary'][len('Node'):
                                                                                                       -len(':0')]
    print('\nEX-PRIMARY NODE HAS BEEN STARTED!')
    print('\nNEW PRIMARY IS {}'.format(primary_after))

    return primary_after


async def demote_primary(pool_handle, wallet_handle, trustee_did):
    try:
        req = await ledger.build_get_validator_info_request(trustee_did)
        results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
        try:
            result = json.loads(sample(results.items(), 1)[0][1])
        except JSONDecodeError:
            try:
                shuffle(list(results.keys()))
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                shuffle(list(results.keys()))
                result = json.loads(sample(results.items(), 1)[0][1])
        name_before = result['result']['data']['Node_info']['Name']
        primary_before =\
            result['result']['data']['Node_info']['Replicas_status'][name_before+':0']['Primary'][len('Node'):
                                                                                                  -len(':0')]
    except TypeError:
        try:
            await asyncio.sleep(120)
            req = await ledger.build_get_validator_info_request(trustee_did)
            results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
            try:
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                try:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
                except JSONDecodeError:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
            name_before = result['result']['data']['Node_info']['Name']
            primary_before = \
                result['result']['data']['Node_info']['Replicas_status'][name_before + ':0']['Primary'][len('Node'):
                                                                                                        -len(':0')]
        except TypeError:
            await asyncio.sleep(240)
            req = await ledger.build_get_validator_info_request(trustee_did)
            results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
            try:
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                try:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
                except JSONDecodeError:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
            name_before = result['result']['data']['Node_info']['Name']
            primary_before = \
                result['result']['data']['Node_info']['Replicas_status'][name_before + ':0']['Primary'][len('Node'):
                                                                                                        -len(':0')]
    res = json.loads(results['Node'+primary_before])
    target_did = res['result']['data']['Node_info']['did']
    alias = res['result']['data']['Node_info']['Name']
    demote_data = json.dumps({'alias': alias, 'services': []})
    demote_req = await ledger.build_node_request(trustee_did, target_did, demote_data)
    demote_res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, demote_req))
    assert demote_res['op'] == 'REPLY'
    print('\nPRIMARY NODE {} HAS BEEN DEMOTED!'.format(primary_before))

    return primary_before, target_did, alias


async def promote_primary(pool_handle, wallet_handle, trustee_did, primary_before, alias, target_did):
    promote_data = json.dumps({'alias': alias, 'services': ['VALIDATOR']})
    promote_req = await ledger.build_node_request(trustee_did, target_did, promote_data)
    promote_res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, promote_req))
    if promote_res['op'] != 'REPLY':
        await asyncio.sleep(60)
        promote_res = json.loads(
            await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, promote_req))
    print(promote_res)
    host = testinfra.get_host('docker://node'+primary_before)
    host.run('systemctl restart indy-node')
    assert promote_res['op'] == 'REPLY'
    print('\nEX-PRIMARY NODE HAS BEEN PROMOTED AND RESTARTED!')

    try:
        req = await ledger.build_get_validator_info_request(trustee_did)
        results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
        try:
            result = json.loads(sample(results.items(), 1)[0][1])
        except JSONDecodeError:
            try:
                shuffle(list(results.keys()))
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                shuffle(list(results.keys()))
                result = json.loads(sample(results.items(), 1)[0][1])
        name_after = result['result']['data']['Node_info']['Name']
        primary_after =\
            result['result']['data']['Node_info']['Replicas_status'][name_after+':0']['Primary'][len('Node'):-len(':0')]
    except TypeError:
        try:
            await asyncio.sleep(120)
            req = await ledger.build_get_validator_info_request(trustee_did)
            results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
            try:
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                try:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
                except JSONDecodeError:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
            name_after = result['result']['data']['Node_info']['Name']
            primary_after = \
                result['result']['data']['Node_info']['Replicas_status'][name_after + ':0']['Primary'][len('Node'):
                                                                                                       -len(':0')]
        except TypeError:
            await asyncio.sleep(240)
            req = await ledger.build_get_validator_info_request(trustee_did)
            results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
            try:
                result = json.loads(sample(results.items(), 1)[0][1])
            except JSONDecodeError:
                try:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
                except JSONDecodeError:
                    shuffle(list(results.keys()))
                    result = json.loads(sample(results.items(), 1)[0][1])
            name_after = result['result']['data']['Node_info']['Name']
            primary_after = \
                result['result']['data']['Node_info']['Replicas_status'][name_after + ':0']['Primary'][len('Node'):
                                                                                                       -len(':0')]
    print('\nNEW PRIMARY IS {}'.format(primary_after))

    return primary_after


def get_pool_info(primary: str) -> dict:
    host = testinfra.get_host('ssh://node{}'.format(primary))
    pool_info = host.run('read_ledger --type=pool').stdout.split('\n')[:-1]
    pool_info = [json.loads(item) for item in pool_info]
    pool_info = {item['txn']['data']['data']['alias']: item['txn']['data']['dest'] for item in pool_info}
    return pool_info


def get_node_alias(node_num):
    return 'Node{}'.format(node_num)


def get_node_did(node_alias, pool_info=None):
    if pool_info is None:
        pool_info = get_pool_info('1')
    return pool_info[node_alias]


async def get_primary(pool_handle, wallet_handle, trustee_did):

    async def _get_primary():
        req = await ledger.build_get_validator_info_request(trustee_did)
        results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
        # remove all timeout entries
        try:
            for i in range(len(results)):
                results.pop(list(results.keys())[list(results.values()).index('timeout')])
        except ValueError:
            pass
        # remove all not REPLY and empty (not selected) primaries entries
        results = {key: json.loads(results[key]) for key in results if
                   (json.loads(results[key])['op'] == 'REPLY')
                   & (json.loads(results[key])['result']['data']['Node_info']['Replicas_status'][key + ':0']['Primary']
                      is not None)}
        # get primaries numbers from all nodes
        primaries = [results[key]['result']['data']['Node_info']['Replicas_status'][key + ':0']['Primary']
                     [len('Node'):-len(':0')] for key in results]
        # count the same entries
        primaries = Counter(primaries)
        return max(primaries, key=primaries.get)

    primary = await eventually(_get_primary, retry_wait=10, timeout=480)
    alias = get_node_alias(primary)
    return primary, alias, get_node_did(alias)


async def demote_random_node(pool_handle, wallet_handle, trustee_did):
    req = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    try:
        result = json.loads(sample(results.items(), 1)[0][1])
    except JSONDecodeError:
        try:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
        except JSONDecodeError:
            shuffle(list(results.keys()))
            result = json.loads(sample(results.items(), 1)[0][1])
    alias = result['result']['data']['Node_info']['Name']
    target_did = result['result']['data']['Node_info']['did']
    demote_data = json.dumps({'alias': alias, 'services': []})
    demote_req = await ledger.build_node_request(trustee_did, target_did, demote_data)
    demote_res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, demote_req))
    # while demote_res['op'] != 'REPLY':
    #     demote_res = json.loads(
    #         await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, demote_req))
    assert demote_res['op'] == 'REPLY'

    return alias, target_did


async def demote_node(pool_handle, wallet_handle, trustee_did, alias, target_did):
    demote_data = json.dumps({'alias': alias, 'services': []})
    demote_req = await ledger.build_node_request(trustee_did, target_did, demote_data)
    demote_res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, demote_req))
    # while demote_res['op'] != 'REPLY':
    #     demote_res = json.loads(
    #         await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, demote_req))
    assert demote_res['op'] == 'REPLY'


async def promote_node(pool_handle, wallet_handle, trustee_did, alias, target_did):
    promote_data = json.dumps({'alias': alias, 'services': ['VALIDATOR']})
    promote_req = await ledger.build_node_request(trustee_did, target_did, promote_data)
    promote_res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, promote_req))
    # while promote_res['op'] != 'REPLY':
    #     promote_res = json.loads(
    #         await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, promote_req))
    host = testinfra.get_host('ssh://node'+alias[4:])
    host.run('systemctl restart indy-node')
    assert promote_res['op'] == 'REPLY'


# TODO replace with eventually
async def eventually_positive(func, *args, cycles_limit=15, sleep=30, **kwargs):
    # this is for check_pool_is_in_sync, promote_node, demote_node and other self-asserted functions
    cycles = 0
    while True:
        try:
            await asyncio.sleep(sleep)
            cycles += 1
            res = await func(*args, **kwargs)
            print('NO ERRORS HERE SO BREAK THE LOOP!')
            break
        except AssertionError or IndyError:
            if cycles >= cycles_limit:
                print('CYCLES LIMIT IS EXCEEDED BUT LEDGERS ARE NOT IN SYNC!')
                raise AssertionError
            else:
                pass
    return res


# TODO replace with eventually
async def write_eventually_positive(func, *args, cycles_limit=40):
    cycles = 0
    res = dict()
    res['op'] = ''
    while res['op'] != 'REPLY':
        try:
            cycles += 1
            if cycles >= cycles_limit:
                print('CYCLES LIMIT IS EXCEEDED!')
                break
            res = await func(*args)
            await asyncio.sleep(10)
        except IndyError:
            await asyncio.sleep(10)
            pass
    return res


# TODO replace with eventually
async def read_eventually_positive(func, *args, cycles_limit=30):
    cycles = 0
    res = await func(*args)
    while res['result']['seqNo'] is None:
        cycles += 1
        if cycles >= cycles_limit:
            print('CYCLES LIMIT IS EXCEEDED!')
            break
        res = await func(*args)
        await asyncio.sleep(5)
    return res


# TODO replace with eventually
async def eventually_negative(func, *args, cycles_limit=15):
    cycles = 0
    is_exception_raised = False

    while True:
        try:
            await asyncio.sleep(15)
            await func(*args)
            cycles += 1
            if cycles >= cycles_limit:
                print('CYCLES LIMIT IS EXCEEDED BUT EXCEPTION HAS NOT BEEN RAISED!')
                break
        except IndyError:
            print('EXPECTED INDY ERROR HAS BEEN RAISED!')
            is_exception_raised = True
            break

    return is_exception_raised


async def wait_until_vc_is_done(primary_before, pool_handler, wallet_handler, trustee_did, cycles_limit=15, sleep=30):
    cycles = 0
    primary_after = primary_before

    while primary_before == primary_after:
        cycles += 1
        if cycles >= cycles_limit:
            print('CYCLES LIMIT IS EXCEEDED BUT PRIMARY HAS NOT BEEN CHANGED!')
            raise AssertionError
        primary_after, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        await asyncio.sleep(sleep)

    return primary_after


class NodeHost:
    def __init__(self, node_id):
        self._id = node_id
        self._host = testinfra.get_host('ssh://{}'.format(self.name))

    @property
    def name(self):
        return "node{}".format(self._id)

    @property
    def host(self):
        return self._host

    @property
    def id(self):
        return self._id

    def run(self, command: str, print_res=False):
        output = self._host.check_output(command)
        if print_res:
            print(output)
        return output

    def start_service(self):
        return self.run('systemctl start indy-node')

    def stop_service(self):
        return self.run('systemctl stop indy-node')

    def restart_service(self):
        return self.run('systemctl restart indy-node')

    def generate_logs(self):
        # TODO might fail in case of running nodes since tar complaints when
        # files are changed during archiving
        archive_path = "/tmp/{}.{}.tgz".format(self.name, datetime.now().strftime("%Y-%m-%dT%H%M%S"))
        self.run(
            "find /var/log/indy/sandbox/ /var/lib/indy/sandbox/ -maxdepth 1 -type f -not -name data "
            "| tar czf {} -T -"
            .format(archive_path)
        )
        return archive_path


async def send_random_nyms(pool_handle, wallet_handle, submitter_did, count):
    for i in range(count):
        await send_nym(pool_handle, wallet_handle, submitter_did, random_did_and_json()[0], None, None, None)
