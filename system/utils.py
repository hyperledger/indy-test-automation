import json
import string
import random
import base58
from indy import pool, wallet, did, ledger, anoncreds, blob_storage
from ctypes import CDLL
import functools
import asyncio
import testinfra
from random import sample, shuffle
from json import JSONDecodeError
import time
from collections import Counter


def run_async_method(method, *args, **kwargs):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(method(*args, **kwargs))


def random_string(length):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))


def random_did_and_json():
    return base58.b58encode(random_string(16)).decode(),\
        json.dumps({'did': base58.b58encode(random_string(16)).decode()})


def random_seed_and_json():
    return random_string(32), json.dumps({'seed': random_string(32)})


async def pool_helper(pool_name=None, path_to_genesis='../docker_genesis', node_list=None):
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


async def payment_initializer(library_name, initializer_name):
    library = CDLL(library_name)
    init = getattr(library, initializer_name)
    init()


async def nym_helper(pool_handle, wallet_handle, submitter_did, target_did,
                     target_vk=None, target_alias=None, target_role=None):
    req = await ledger.build_nym_request(submitter_did, target_did, target_vk, target_alias, target_role)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def attrib_helper(pool_handle, wallet_handle, submitter_did, target_did, xhash=None, raw=None, enc=None):
    req = await ledger.build_attrib_request(submitter_did, target_did, xhash, raw, enc)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def schema_helper(pool_handle, wallet_handle, submitter_did, schema_name, schema_version, schema_attrs):
    schema_id, schema_json = await anoncreds.issuer_create_schema(submitter_did, schema_name, schema_version,
                                                                  schema_attrs)
    req = await ledger.build_schema_request(submitter_did, schema_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return schema_id, res


async def cred_def_helper(pool_handle, wallet_handle, submitter_did, schema_json, tag, signature_type, config_json):
    cred_def_id, cred_def_json = \
        await anoncreds.issuer_create_and_store_credential_def(wallet_handle, submitter_did, schema_json, tag,
                                                               signature_type, config_json)
    req = await ledger.build_cred_def_request(submitter_did, cred_def_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return cred_def_id, cred_def_json, res


async def revoc_reg_def_helper(pool_handle, wallet_handle, submitter_did, revoc_def_type, tag, cred_def_id, config_json):
    tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
    tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
    revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = \
        await anoncreds.issuer_create_and_store_revoc_reg(wallet_handle, submitter_did, revoc_def_type, tag,
                                                          cred_def_id, config_json, tails_writer_handle)
    req = await ledger.build_revoc_reg_def_request(submitter_did, revoc_reg_def_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json, res


async def revoc_reg_entry_helper(pool_handle, wallet_handle, submitter_did, revoc_def_type, tag, cred_def_id, config_json):
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


async def get_nym_helper(pool_handle, wallet_handle, submitter_did, target_did):
    req = await ledger.build_get_nym_request(submitter_did, target_did)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_attrib_helper(pool_handle, wallet_handle, submitter_did, target_did, xhash=None, raw=None, enc=None):
    req = await ledger.build_get_attrib_request(submitter_did, target_did, raw, xhash, enc)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_schema_helper(pool_handle, wallet_handle, submitter_did, id_):
    req = await ledger.build_get_schema_request(submitter_did, id_)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_cred_def_helper(pool_handle, wallet_handle, submitter_did, id_):
    req = await ledger.build_get_cred_def_request(submitter_did, id_)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_revoc_reg_def_helper(pool_handle, wallet_handle, submitter_did, id_):
    req = await ledger.build_get_revoc_reg_def_request(submitter_did, id_)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_revoc_reg_helper(pool_handle, wallet_handle, submitter_did, id_, timestamp):
    req = await ledger.build_get_revoc_reg_request(submitter_did, id_, timestamp)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def get_revoc_reg_delta_helper(pool_handle, wallet_handle, submitter_did, id_, from_, to_):
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


async def send_and_get_nym(pool_handle, wallet_handle, trustee_did, some_did):
    add = await nym_helper(pool_handle, wallet_handle, trustee_did, some_did)
    while add['op'] != 'REPLY':
        add = await nym_helper(pool_handle, wallet_handle, trustee_did, some_did)
        time.sleep(1)
    assert add['op'] == 'REPLY'

    get = await get_nym_helper(pool_handle, wallet_handle, trustee_did, some_did)
    while get['result']['seqNo'] is None:
        get = await get_nym_helper(pool_handle, wallet_handle, trustee_did, some_did)
        time.sleep(1)
    assert get['result']['seqNo'] is not None


def check_ledger_sync():
    hosts = [testinfra.get_host('ssh://node{}'.format(i)) for i in range(1, 8)]
    pool_results = [host.run('read_ledger --type=pool --count') for host in hosts]
    print('\nPOOL LEDGER SYNC: {}'.format([result.stdout for result in pool_results]))
    config_results = [host.run('read_ledger --type=config --count') for host in hosts]
    print('\nCONFIG LEDGER SYNC: {}'.format([result.stdout for result in config_results]))
    domain_results = [host.run('read_ledger --type=domain --count') for host in hosts]
    print('\nDOMAIN LEDGER SYNC: {}'.format([result.stdout for result in domain_results]))
    audit_results = [host.run('read_ledger --type=audit --count') for host in hosts]
    print('\nAUDIT LEDGER SYNC: {}'.format([result.stdout for result in audit_results]))

    assert all([pool_results[i].stdout == pool_results[i + 1].stdout for i in range(-1, len(pool_results) - 1)])
    assert all([config_results[i].stdout == config_results[i + 1].stdout for i in range(-1, len(config_results) - 1)])
    assert all([domain_results[i].stdout == domain_results[i + 1].stdout for i in range(-1, len(domain_results) - 1)])
    assert all([audit_results[i].stdout == audit_results[i + 1].stdout for i in range(-1, len(audit_results) - 1)])


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
            time.sleep(120)
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
            time.sleep(240)
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
            time.sleep(120)
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
            time.sleep(240)
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
            time.sleep(120)
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
            time.sleep(240)
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
        time.sleep(60)
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
            time.sleep(120)
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
            time.sleep(240)
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


async def get_primary(pool_handle, wallet_handle, trustee_did):
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
    # find actual primary
    primary = max(primaries, key=primaries.get)
    alias = 'Node{}'.format(primary)
    host = testinfra.get_host('ssh://node{}'.format(primary))
    pool_info = host.run('read_ledger --type=pool').stdout.split('\n')[:-1]
    pool_info = [json.loads(item) for item in pool_info]
    pool_info = {item['txn']['data']['data']['alias']: item['txn']['data']['dest'] for item in pool_info}
    target_did = pool_info[alias]

    return primary, alias, target_did


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
    assert demote_res['op'] == 'REPLY'

    return alias, target_did


async def demote_node(pool_handle, wallet_handle, trustee_did, alias, target_did):
    demote_data = json.dumps({'alias': alias, 'services': []})
    demote_req = await ledger.build_node_request(trustee_did, target_did, demote_data)
    demote_res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, demote_req))
    assert demote_res['op'] == 'REPLY'


async def promote_node(pool_handle, wallet_handle, trustee_did, alias, target_did):
    promote_data = json.dumps({'alias': alias, 'services': ['VALIDATOR']})
    promote_req = await ledger.build_node_request(trustee_did, target_did, promote_data)
    promote_res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, promote_req))
    host = testinfra.get_host('ssh://node'+alias[4:])
    host.run('systemctl restart indy-node')
    assert promote_res['op'] == 'REPLY'
