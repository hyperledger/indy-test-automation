import time
from datetime import datetime, timedelta, timezone
import os
import string
from typing import Optional
import subprocess
import base58
import asyncio
from random import sample, shuffle, randrange
from collections import Counter
from collections.abc import Iterable
from inspect import isawaitable
import random
import itertools
import functools
from ctypes import CDLL
import testinfra
import json
from json import JSONDecodeError
import hashlib
from indy import pool, wallet, did, ledger, anoncreds, blob_storage, IndyError, payment


import logging
logger = logging.getLogger(__name__)


MODULE_PATH = os.path.abspath(os.path.dirname(__file__))
POOL_GENESIS_PATH = os.path.join(MODULE_PATH, 'docker_genesis')
EXTRA_DESTS = [
    '4Tn3wZMNCvhSTXPcLinQDnHyj56DTLQtL61ki4jo2Loc',
    '6G9QhQa3HWjRKeRmEvEkLbWWf2t7cw6KLtafzi494G4G',
    'BeLdccGjNcCDpVNCbxCFb4CfZWGxLCSM4CfGFFoZ443V',
    'CJqRrPMjPec5wvHDoggvxYUk13fXDbya3Aopc4TiFkNr',
    'GYUibLwguJX5YcEYmy1xE45j6cbdnSjyJm9bKPiM163Z',
    '67NLWsr8dFJrL6cDWcZkDce4hoSSGPBesk2PzqvGqL1R',
    '4UjwEpgGVqpyovAxFRVP5mn2S4m6UHq2CftzeE73YrNq'
]
EXTRA_BLSKEYS = [
    '2RdajPq6rCidK5gQbMzSJo1NfBMYiS3e44GxjTqZUk3RhBdtF28qEABHRo4MgHS2hwekoLWRTza9XiGEMRCompeujWpX85MPt87WdbTMysXZfb7J1ZXUEMrtE5aZahfx6p2YdhZdrArFvTmFWdojaD2V5SuvuaQL4G92anZ1yteay3R',
    'zi65fRHZjK2R8wdJfDzeWVgcf9imXUsMSEY64LQ4HyhDMsSn3Br1vhnwXHE7NyGjxVnwx4FGPqxpzY8HrQ2PnrL9tu4uD34rjgPEnFXnsGAp8aF68R4CcfsmUXfuU51hogE7dZCvaF9GPou86EWrTKpW5ow3ifq16Swpn5nKMXHTKj',
    'oApJaiaS9tKPGxb7svdDWvRSKYKFE8mFJVQyEQsRRqUMDeFQwLqRgrtxNfCtYrunCjzFmaMjFDnSy8a5n1ZCpp3TGH8oXJ8s4i7H9Yiy5hz2uPc3ManS9HiTvQE3TcBfxkuXswmR3Esy9Qi7LUjCuWGoi7fkwB3wATcLMJ5AuYr8mB',
    '4ZaPVUjKWct8pQ3NJxC3GDA9LZqk8bPLaLmncBCPk33NbQnF1FyAvkkfj2Kmh1BbrJN6eXH6suGTvPFkrpSyLcmyp9CHJoiibdXi6mKEftNBbekepf7vzGvAmqgybzcPy1dqrykWyKVVQPQwmXXtGqNB2eafuwx8TECWakJHcJTA6AC',
    '2ngTBQLDh78H3o7u7FpZMUgcpjuQ4brqh5v2bEj3Xs84GGVpnAbihmdQcsba8WNwrvBK6ScPa8kLLfKikZBmsVtFpPxPjD9rdT8YsGrSnYCkJARr2DKzyupKDqVncVY7ahg8Q1cDeqqgbdZwGnaAA1gSKNWjH2LRNaXF2dYh2Gjkrdo',
    'CETPJiNq31ezYnoYt3eTZU16NnjjH4k3LsTRidC3rMueVc9Kh8MxfwD1wmUuZ11eNM8bVgxb6nnZc7m7RA8QyRbeQV4MErKAFjg7CfrtvAoXA5Cffg8izYKAqt8XGPuJFW1Eozuzuw9SMSHaLKeVWTJiSSAAWSsn7zBP43HVZ5EaH3',
    '28jA1xmLrYafA6rkMnTCRY66pnCj852jiVdta22k5W3R5XpXAVsPFvLu4RuKqGB1kb1ZVJqUuLF33cTjRzwRfvkzH9TYa8YNbvSayxtNioJMA5fSAkYmApAMPqHxJKZRoDtQbQ57ZDNGuJUGa7sQhdWdEDZD112N9eCmQEkcepQDswF'
]
EXTRA_BLSKEY_POPS = [
    'RbGAR89T5bg6Bg66Xg1fy5NjVarmvr8Q7XAmEPCA6arPvcfcDwLiEftD2cCVoEnrRSPLhgf3Cn9n81gdgMCbSBEhKuWW3njXkPFE1jvP67bU1d2jb6gw5BxyxsF9qg1Hvz6pr181u7s1WZBmGXinLoKaFhb6jptHghHvtqEuTgoqXM',
    'QocoFNfnfbFxLobP9DeUgH2gDPc3FjB44JpfnHo9RosCDubw6AJeRj84avhBKpFqxuVQMpyXwPZ5uPVGfdadsjywrLsfABoeBw1JAvDckzAjaKDvhu1K7LX8zpzaQewWmt8VcWovyiaDJDDSdJQycvfQxzWk5G93iP26zwAriq7wYK',
    'QqURauAZ5zhjW9yVMtGxTLLDfnAxAhavzmuSUmMosmVZLSkcYEcywHHaxi7axkpRJmsg4kmeZk1tzC4zUQrRDLc7FgcfCuTN15ub3JkynAh29x76nr7KxeHWLwMZVMyzMc5fiUfxWk2RbChitZmbbzqTVQSpjodh8TJgZX4b5p9ap7',
    'RSZ6uTEGrXkzRMFztZRQkFJCH13BJFZC7G5DqF8K7J5YoHYsdaTzSQqGDjKaUMcuRuiUsTUta8udcF31JFJpszNzqdxTUjy5fAVFd2h2U2xW6SiucjGKGP88uNnx4eWv28P4HpaCd7A3cPxfnWpnpCtywRguqFa4TRurYZK5eTW7XM',
    'Rbe2kBioQxNvxcbn46oe31AjDBdMMBjSgZfsN3jhfyK4r7512h815HKugx7ttr6z3AKCQmXJMz3EWPMKZMDe8Km1od1p2oiURNPjhT56jjKhkhGUzm91ndgUaM7MctGmdGJJC2R65uorvhNa7mckm76r3rvLW2ZGQd4f4YfavYsFDq',
    'REr2qjuvUcJbYVhtoqgBpvAZPyELwRvsAsNhQHhhLbo522qekXN26pjHvbVkS65QgBc2pMJY1MU7fXybhomMAdgn3FzSYT3mA6h9XqqfcQ938Mfuh6BmEeLGvAKHx3rXYm6y2hvQR3a5oFM2qXdWyGyqvzafnbcscy33NTBbSihJMd',
    'RTZ3YMzzhsjeXkXieyhnvYdpLGBrEwcJWd3tDcX74EBTtghzW53DaVsYF4M5be6YBuLTGNiZkbzV7AhQ4gjtjsk8t6RFPPxxGtFxQMUNjPrRdJWwGrynTpRuk3vxWy1XKpmd5hEaauXNJdBLdj5cRFCae6WkqYTqbQN3kxpF3dd7cT'
]

PERSISTENT_INSTANCES = {
    'ap-northeast-1': ['i-07813055c26ecf5d2', 'i-0ba6de7b7e4ac763a'],
    'ap-northeast-2': ['i-0d2d372e6a3c5e017'],
    'ap-southeast-1': ['i-0ca3f7bf60d60d133', 'i-06836b3ffe6aaca39'],
    'ap-southeast-2': ['i-0aaed544f37ee52c1', 'i-0fcb2d529e3f9a04f'],
    'ca-central-1': ['i-03078455ca5dda6b8', 'i-00cd5b1dca8a078e1'],
    'eu-central-1': ['i-06d864ffc17f20f94', 'i-0d38585877dc14755'],
    'eu-west-1': ['i-06f30f8aed3af1d4c', 'i-058781262b6761fdc'],
    'eu-west-2': ['i-0f6dedb3ee93e1138'],
    'sa-east-1': ['i-0eb6a38d4fe2d47a5', 'i-08a30f8a12db050f9'],
    'us-east-1': ['i-06784287da28fa930', 'i-0995b5b9f320a2824', 'i-0d1b2f330f139ea85'],
    'us-east-2': ['i-0eb04f156b1c51b14', 'i-07cdbd66e43be4296'],
    'us-west-1': ['i-043ba82aa40f0fdae', 'i-0db8a21e6c0252ba7'],
    'us-west-2': ['i-042ee39c972737df7', 'i-0852c0983a638d6d9']
}

ORIGINAL_MAPPING = {
    'i-06d864ffc17f20f94': 'vol-0379428547d514ae2',
    'i-0d38585877dc14755': 'vol-02999333a7b1b652a',
    'i-07813055c26ecf5d2': 'vol-0d4cdb4f0412443c7',
    'i-0ba6de7b7e4ac763a': 'vol-0f311b05f1796e963',
    'i-0f6dedb3ee93e1138': 'vol-0f36900112bf52107',
    'i-043ba82aa40f0fdae': 'vol-05c8b4c04926b8f9e',
    'i-0db8a21e6c0252ba7': 'vol-0bc80bbae343c430e',
    'i-06784287da28fa930': 'vol-0560016eb5ce57e2c',
    'i-0995b5b9f320a2824': 'vol-0210a9f59477b7c7c',
    'i-0d1b2f330f139ea85': 'vol-05512ff56b9f8bdcd',
    'i-0ca3f7bf60d60d133': 'vol-0aebb232089ec39ff',
    'i-06836b3ffe6aaca39': 'vol-01a8207bfa16a9ebc',
    'i-06f30f8aed3af1d4c': 'vol-05dd0abe9eb45e7a8',
    'i-058781262b6761fdc': 'vol-0f3072109275366fc',
    'i-042ee39c972737df7': 'vol-0fd523fd76be9cdcb',
    'i-0852c0983a638d6d9': 'vol-08a17642f64d89870',
    'i-0aaed544f37ee52c1': 'vol-0ac4868972e68a32d',
    'i-0fcb2d529e3f9a04f': 'vol-079586732947212a2',
    'i-0eb04f156b1c51b14': 'vol-0fc5e91eca4f535af',
    'i-07cdbd66e43be4296': 'vol-0d8ab5f28f6212612',
    'i-03078455ca5dda6b8': 'vol-07cc1de112cd2fabd',
    'i-00cd5b1dca8a078e1': 'vol-01003e71e0349d6d6',
    'i-0eb6a38d4fe2d47a5': 'vol-04999b7fb69739f54',
    'i-08a30f8a12db050f9': 'vol-0f7a5863cb7942141',
    'i-0d2d372e6a3c5e017': 'vol-0accc7c6548af7a7a'
}

UPGRADE_MAPPING = {
    'i-06d864ffc17f20f94': 'vol-0b7e077fadb734c87',  # 4
    'i-0d38585877dc14755': 'vol-04a3448e6c085ee66',  # 17
    'i-07813055c26ecf5d2': 'vol-0d4483214a8704ca9',  # 18
    'i-0ba6de7b7e4ac763a': 'vol-053b193d3d48bb8cd',  # 5
    'i-0f6dedb3ee93e1138': 'vol-0158c5a3ab37bb971',  # 13
    'i-043ba82aa40f0fdae': 'vol-0d1c39ed7455978c4',  # 14
    'i-0db8a21e6c0252ba7': 'vol-0ade27a5cb797295a',  # 1
    'i-06784287da28fa930': 'vol-0ff8a237befeb4ee4',  # 24
    'i-0995b5b9f320a2824': 'vol-074ff705972c71a4c',  # 10
    'i-0d1b2f330f139ea85': 'vol-018cf3d9b780d3832',  # 23
    'i-0ca3f7bf60d60d133': 'vol-0f254e8c98d02f39a',  # 6
    'i-06836b3ffe6aaca39': 'vol-08a50535d8574a39b',  # 19
    'i-06f30f8aed3af1d4c': 'vol-0b22d27e96c235e46',  # 16
    'i-058781262b6761fdc': 'vol-084cca5bcbe68879b',  # 3
    'i-042ee39c972737df7': 'vol-0ff01f694f80c9da4',  # 22
    'i-0852c0983a638d6d9': 'vol-06bf54fbaf725dc35',  # 12
    'i-0aaed544f37ee52c1': 'vol-0c540717bb7a38ccc',  # 20
    'i-0fcb2d529e3f9a04f': 'vol-0df295c3d22c66086',  # 7
    'i-0eb04f156b1c51b14': 'vol-080722e515a1a8cc6',  # 21
    'i-07cdbd66e43be4296': 'vol-03fe70c18c11b2c0d',  # 11
    'i-03078455ca5dda6b8': 'vol-0ecf4062af6687d77',  # 15
    'i-00cd5b1dca8a078e1': 'vol-0154433c7dd85b4e9',  # 2
    'i-0eb6a38d4fe2d47a5': 'vol-0c304466dc5e2228e',  # 9
    'i-08a30f8a12db050f9': 'vol-023a5172007ecf06f',  # 25
    'i-0d2d372e6a3c5e017': 'vol-023d59d0b6a6b6d6a'  # 8
}

docker_7_destinations = [
    'Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv', '8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb',
    'DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya', '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA',
    '4SWokCJWJc69Tn74VvLS6t2G2ucvXqM9FDMsWJjmsUxe', 'Cv1Ehj43DDM5ttNBmC6VPpEfwXWwfGktHwjDJsTV5Fz8',
    'BM8dTooz5uykCbYSAAFwKNkYfT4koomBHsSWHTDtkjhW'
]

docker_7_schedule = json.dumps(
    dict(
        {
            dest: datetime.strftime(
                datetime.now(tz=timezone.utc) + timedelta(minutes=5 + i * 5), '%Y-%m-%dT%H:%M:%S%z'
            ) for dest, i in zip(docker_7_destinations, range(len(docker_7_destinations)))
        }
    )
)


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
    REQ_TIMEOUT = 5
    if not pool_name:
        pool_name = random_string(25)
    if node_list:
        pool_config = json.dumps(
            {"genesis_txn": path_to_genesis, "preordered_nodes": node_list, "timeout": REQ_TIMEOUT}
        )
    else:
        pool_config = json.dumps({"genesis_txn": path_to_genesis, "timeout": REQ_TIMEOUT})
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


async def send_nym(
        pool_handle, wallet_handle, submitter_did, target_did, target_vk=None, target_alias=None, target_role=None
):
    req = await ledger.build_nym_request(submitter_did, target_did, target_vk, target_alias, target_role)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def send_attrib(
        pool_handle, wallet_handle, submitter_did, target_did, xhash=None, raw=None, enc=None
):
    req = await ledger.build_attrib_request(submitter_did, target_did, xhash, raw, enc)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return res


async def send_schema(
        pool_handle, wallet_handle, submitter_did, schema_name, schema_version, schema_attrs
):
    schema_id, schema_json = await anoncreds.issuer_create_schema(
        submitter_did, schema_name, schema_version, schema_attrs
    )
    req = await ledger.build_schema_request(submitter_did, schema_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return schema_id, res


async def send_cred_def(
        pool_handle, wallet_handle, submitter_did, schema_json, tag, signature_type, config_json
):
    cred_def_id, cred_def_json = await anoncreds.issuer_create_and_store_credential_def(
        wallet_handle, submitter_did, schema_json, tag, signature_type, config_json
    )
    req = await ledger.build_cred_def_request(submitter_did, cred_def_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return cred_def_id, cred_def_json, res


async def send_revoc_reg_def(
        pool_handle, wallet_handle, submitter_did, revoc_def_type, tag, cred_def_id, config_json
):
    tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
    tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
    revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = await anoncreds.issuer_create_and_store_revoc_reg(
        wallet_handle, submitter_did, revoc_def_type, tag, cred_def_id, config_json, tails_writer_handle
    )
    req = await ledger.build_revoc_reg_def_request(submitter_did, revoc_reg_def_json)
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))

    return revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json, res


async def send_revoc_reg_entry(
        pool_handle, wallet_handle, submitter_did, revoc_def_type, tag, cred_def_id, config_json
):
    tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
    tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
    revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = await anoncreds.issuer_create_and_store_revoc_reg(
        wallet_handle, submitter_did, revoc_def_type, tag, cred_def_id, config_json, tails_writer_handle
    )
    req = await ledger.build_revoc_reg_def_request(submitter_did, revoc_reg_def_json)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req)
    req = await ledger.build_revoc_reg_entry_request(
        submitter_did, revoc_reg_def_id, revoc_def_type, revoc_reg_entry_json
    )
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
        try:
            result = host.run('journalctl -u indy-node.service -b -p info')
        except AssertionError:
            print('Node is unreachable!')
            result = ''
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
    pool_handle, wallet_handle, trustee_did, nyms_count=1, timeout=30
):
    writes = await check_pool_performs_write(
        pool_handle, wallet_handle, trustee_did, nyms_count=nyms_count
    )
    dids = [resp['result']['txn']['data']['dest'] for resp in writes]
    return await eventually(
        check_pool_performs_read, pool_handle, wallet_handle, trustee_did, dids, timeout=timeout
    )


async def ensure_pool_performs_write_read(
    pool_handle, wallet_handle, trustee_did, nyms_count=1, timeout=30
):
    await eventually(
        check_pool_performs_write_read, pool_handle, wallet_handle, trustee_did, nyms_count=nyms_count, timeout=timeout
    )


async def check_pool_is_functional(
    pool_handle, wallet_handle, trustee_did, nyms_count=3
):
    await check_pool_performs_write_read(
        pool_handle, wallet_handle, trustee_did, nyms_count=nyms_count
    )


async def ensure_pool_is_functional(
    pool_handle, wallet_handle, trustee_did, nyms_count=1, timeout=30
):
    await ensure_pool_performs_write_read(
        pool_handle, wallet_handle, trustee_did, nyms_count=nyms_count, timeout=timeout
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
    token_results = [host.run('read_ledger --type=sovtoken --count') for host in hosts]
    print('\nTOKEN LEDGER SYNC: {}'.format([result for result in token_results]))

    for res in (pool_results, config_results, domain_results, audit_results, token_results):
        assert len(set(res)) == 1


async def ensure_pool_is_in_sync(node_ids=None, nodes_num=7):
    await eventually(
        check_pool_is_in_sync, node_ids=node_ids, nodes_num=nodes_num, retry_wait=10, timeout=200
    )


async def check_primary_changed(pool_handler, wallet_handler, trustee_did, primary_before):
    primary_after, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
    assert primary_after != primary_before
    return primary_after


async def ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_before):
    return await eventually(
        check_primary_changed, pool_handler, wallet_handler, trustee_did, primary_before, retry_wait=20, timeout=600
    )


async def check_all_nodes_online(pool_handle, wallet_handle, trustee_did, unreached=0):
    results = await get_validator_info(pool_handle, wallet_handle, trustee_did)
    assert all([v['result']['data']['Pool_info']['Unreachable_nodes_count'] == unreached for k, v in results.items()])


async def ensure_all_nodes_online(pool_handle, wallet_handle, trustee_did, unreached=0):
    await eventually(
        check_all_nodes_online, pool_handle, wallet_handle, trustee_did, unreached, retry_wait=10, timeout=200
    )


async def check_state_root_hashes_are_in_sync(pool_handle, wallet_handle, trustee_did):
    results = await get_validator_info(pool_handle, wallet_handle, trustee_did)
    committed_state_roots = [
        v['result']['data']['Node_info']['Committed_state_root_hashes'] for k, v in results.items()
    ]
    uncommitted_state_roots = [
        v['result']['data']['Node_info']['Uncommitted_state_root_hashes'] for k, v in results.items()
    ]
    assert all([a == b for a, b in itertools.combinations(committed_state_roots, 2)])
    assert all([a == b for a, b in itertools.combinations(uncommitted_state_roots, 2)])


async def ensure_state_root_hashes_are_in_sync(pool_handle, wallet_handle, trustee_did):
    await eventually(
        check_state_root_hashes_are_in_sync, pool_handle, wallet_handle, trustee_did, retry_wait=10, timeout=200
    )


async def check_ledgers_are_in_sync(pool_handle, wallet_handle, trustee_did):
    results = await get_validator_info(pool_handle, wallet_handle, trustee_did)
    transaction_count = [
        v['result']['data']['Node_info']['Metrics']['transaction-count'] for k, v in results.items()
    ]
    assert all([a == b for a, b in itertools.combinations(transaction_count, 2)])


async def ensure_ledgers_are_in_sync(pool_handle, wallet_handle, trustee_did):
    await eventually(
        check_ledgers_are_in_sync, pool_handle, wallet_handle, trustee_did, retry_wait=10, timeout=200
    )


async def ensure_pool_is_okay(pool_handle, wallet_handle, trustee_did):
    await ensure_all_nodes_online(pool_handle, wallet_handle, trustee_did)
    await ensure_ledgers_are_in_sync(pool_handle, wallet_handle, trustee_did)
    await ensure_state_root_hashes_are_in_sync(pool_handle, wallet_handle, trustee_did)


async def get_validator_info(pool_handle, wallet_handle, trustee_did):
    req = await ledger.build_get_validator_info_request(trustee_did)
    results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    # remove all timeout entries
    try:
        for i in range(len(results)):
            results.pop(list(results.keys())[list(results.values()).index('timeout')])
    except ValueError:
        pass
    results = {k: json.loads(v) for k, v in results.items()}
    return results


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


# noinspection PyUnusedLocal
def get_node_did(node_alias, pool_info=None, primary=None):
    if pool_info is None:
        try:
            pool_info = get_pool_info(primary)
            temp = pool_info[node_alias]
        except KeyError:
            try:
                pool_info = get_pool_info(str(int(primary) + 1))
                temp = pool_info[node_alias]
            except KeyError:
                pool_info = get_pool_info(str(int(primary) - 1))

    print(pool_info)  # print pool info to debug
    return pool_info[node_alias]


async def get_primary(pool_handle, wallet_handle, trustee_did):

    async def _get_primary():

        def get_primary_from_info(info: str, name: str) -> Optional[str]:
            parsed_info = json.loads(info)
            if parsed_info['op'] != 'REPLY':
                return None
            replica_name = parsed_info['result']['data']['Node_info']['Replicas_status'][name + ':0']['Primary']
            if replica_name is None:
                return None
            return replica_name[len('Node'):-len(':0')]

        def get_vc_status_from_info(info: str) -> Optional[bool]:
            parsed_info = json.loads(info)
            if parsed_info['op'] != 'REPLY':
                return None
            vc_status = parsed_info['result']['data']['Node_info']['View_change_status']['VC_in_progress']
            return vc_status

        req = await ledger.build_get_validator_info_request(trustee_did)
        results = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
        # get n
        n = len(results)
        # calculate f
        f = (n - 1) // 3
        # remove all timeout entries
        try:
            for i in range(len(results)):
                results.pop(list(results.keys())[list(results.values()).index('timeout')])
        except ValueError:
            pass
        # check that VC is not in progress (status `False`)
        assert all([not get_vc_status_from_info(info) for _, info in results.items()])
        # remove all not REPLY and empty (not selected) primaries entries
        primaries = [get_primary_from_info(info, name) for name, info in results.items()]
        # count the same entries
        primaries = Counter(primaries)
        res, votes = primaries.most_common()[0]
        assert res is not None
        assert votes >= (n - f)

        return res

    primary = await eventually(_get_primary, retry_wait=20, timeout=300)
    alias = get_node_alias(primary)
    return primary, alias, get_node_did(alias, primary=primary)


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
    assert promote_res['op'] == 'REPLY'
    host = testinfra.get_host('ssh://node'+alias[4:])
    host.run('systemctl restart indy-node')


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
        # TODO might fail in case of running nodes since tar complaints when files are changed during archiving
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


async def send_node(
        pool_handle, wallet_handle, services, steward_did, node_dest, alias,
        blskey=None, blskey_pop=None, client_ip=None, client_port=None, node_ip=None, node_port=None
):
    data = json.dumps(
        {
            'alias': alias,
            'blskey': blskey,
            'blskey_pop': blskey_pop,
            'client_ip': client_ip,
            'client_port': client_port,
            'node_ip': node_ip,
            'node_port': node_port,
            'services': services
        }
    )
    req = await ledger.build_node_request(steward_did, node_dest, data)
    res = json.loads(
        await ledger.sign_and_submit_request(pool_handle, wallet_handle, steward_did, req)
    )

    return res

    # TODO implement helpers to get buildernet and stn genesis files from sovrin repo


async def get_payment_sources(pool_handle, wallet_handle, address):
    payment_method = 'sov'
    req, _ = await payment.build_get_payment_sources_request(wallet_handle, None, address)
    res = await ledger.submit_request(pool_handle, req)
    res = json.loads(await payment.parse_get_payment_sources_response(payment_method, res))
    source = res[0]['source']
    amount = res[0]['amount']

    return source, amount


# use it for shell commands with pipe
def run_external_cmd(cmd):
    ret = subprocess.run(cmd,
                         shell=True,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         timeout=5)
    return ret.stdout.decode().strip().splitlines()


def update_config(string_to_push, nodes_num):
    test_nodes = [NodeHost(i) for i in range(1, nodes_num+1)]
    path_to_config = '/etc/indy/indy_config.py'
    separator = "echo ' '"
    update_res = [
        node.run("{} >> {} && echo {} >> {}".format(separator, path_to_config, string_to_push, path_to_config))
        for node in test_nodes
    ]
    assert all(res == '' for res in update_res)
    restart_res = [node.restart_service() for node in test_nodes]
    assert all(res == '' for res in restart_res)


async def send_payments(pool_handle, wallet_handle, submitter_did, address_from, count):
    payment_method = 'sov'

    for i in range(1, count+1):
        address_to = await payment.create_payment_address(wallet_handle, payment_method, json.dumps({}))
        source, amount = await get_payment_sources(pool_handle, wallet_handle, address_from)
        print(source, amount)
        req, _ = await payment.build_payment_req(
            wallet_handle, submitter_did, json.dumps([source]), json.dumps(
                [
                    {'recipient': address_to, 'amount': 100000},
                    {'recipient': address_from, 'amount': amount - 100000}
                ]
            ), None
        )
        res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, submitter_did, req))
        if res['op'] == 'REJECT' and 'InvalidFundsError' in res['reason']:
            pass  # handle bad payment source from lagged node due to state proof reading
        else:
            assert res['op'] == 'REPLY'


async def send_nodes(pool_handle, wallet_handle, trustee_did, count, alias=None):
    # create single STEWARD to add ALIAS node once and change it by NODE txns
    steward_did, steward_vk = await did.create_and_store_my_did(
        wallet_handle, json.dumps({'seed': '00000000000000000000000Steward99'})
    )
    await send_nym(pool_handle, wallet_handle, trustee_did, steward_did, steward_vk, None, 'STEWARD')

    for i in range(1, count+1):
        if not alias:  # create new STEWARD for each NODE txn
            steward_did, steward_vk = await did.create_and_store_my_did(wallet_handle, '{}')
            await send_nym(pool_handle, wallet_handle, trustee_did, steward_did, steward_vk, None, 'STEWARD')
        req = await ledger.build_node_request(
            steward_did, steward_vk, json.dumps(
                {
                    'alias': alias if alias else '{}_{}'.format(random_string(10), i),
                    'client_ip': '{}.{}.{}.{}'.format(randrange(1, 255), 0, 0, randrange(1, 255)),
                    'client_port': randrange(1, 32767),
                    'node_ip': '{}.{}.{}.{}'.format(randrange(1, 255), 0, 0, randrange(1, 255)),
                    'node_port': randrange(1, 32767),
                    'services': []
                }
            )
        )
        res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, steward_did, req))
        assert res['op'] == 'REPLY'


async def send_upgrades(pool_handle, wallet_handle, trustee_did, package_name, count):
    if package_name == 'indy-node':
        version = '9.99.9.dev9999'
    elif package_name == 'sovrin':
        version = '9.9.999'
    else:
        raise NameError('Invalid package name!')
    dests = [
        'Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv', '8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb',
        'DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya', '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA',
        '4SWokCJWJc69Tn74VvLS6t2G2ucvXqM9FDMsWJjmsUxe', 'Cv1Ehj43DDM5ttNBmC6VPpEfwXWwfGktHwjDJsTV5Fz8',
        'BM8dTooz5uykCbYSAAFwKNkYfT4koomBHsSWHTDtkjhW'
    ]
    docker_7_schedule = json.dumps(
        dict(
            {dest: datetime.strftime(datetime.now(tz=timezone.utc) + timedelta(minutes=999+i*5), '%Y-%m-%dT%H:%M:%S%z')
             for dest, i in zip(dests, range(len(dests)))}
        )
    )
    for i in range(1, count+1):
        req = await ledger.build_pool_upgrade_request(
            trustee_did,
            '{}_{}'.format(random_string(10), i),
            version,
            'start',
            hashlib.sha256().hexdigest(),
            5,
            docker_7_schedule,
            None,
            True,
            True,
            package_name
        )
        res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
        assert res['op'] == 'REPLY'


async def check_get_something(func_name, *args):
    res = await func_name(*args)
    assert res['result']['seqNo'] is not None
    return res


async def ensure_get_something(func_name, *args):
    res = await eventually(check_get_something, func_name, *args)
    return res


async def check_cant_get_something(func_name, *args):
    res = await func_name(*args)
    assert res['result']['seqNo'] is None
    return res


async def ensure_cant_get_something(func_name, *args):
    res = await eventually(check_cant_get_something, func_name, *args)
    return res


def upgrade_nodes_manually(containers, sovrin_ver, node_ver, plenum_ver, plugin_ver):

    for container in containers:

        assert container.exec_run(
            ['systemctl', 'stop', 'indy-node'],
            user='root'
        ).exit_code == 0

    for container in containers:

        assert container.exec_run(
            ['apt', 'update'],
            user='root'
        ).exit_code == 0

        assert container.exec_run(
            ['apt', 'install',
             '{}={}'.format('sovrin', sovrin_ver),
             '{}={}'.format('indy-node', node_ver),
             '{}={}'.format('indy-plenum', plenum_ver),
             '{}={}'.format('sovtoken', plugin_ver),
             '{}={}'.format('sovtokenfees', plugin_ver),
             '-y', '--allow-change-held-packages'],
            user='root'
        ).exit_code == 0

    for container in containers:

        assert container.exec_run(
            ['systemctl', 'start', 'indy-node'],
            user='root'
        ).exit_code == 0


async def fees_setter(
        pool_handle, wallet_handle, trustee_did, libsovtoken_payment_method, fees=None
):
    trustee_did2, trustee_vk2 = await did.create_and_store_my_did(
        wallet_handle, json.dumps({"seed": str('000000000000000000000000Trustee2')})
    )
    trustee_did3, trustee_vk3 = await did.create_and_store_my_did(
        wallet_handle, json.dumps({"seed": str('000000000000000000000000Trustee3')})
    )

    res = await send_nym(pool_handle, wallet_handle, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
    assert res['op'] == 'REPLY'
    res = await send_nym(pool_handle, wallet_handle, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
    assert res['op'] == 'REPLY'

    # set fees
    if not fees:
        fees = {
            'nym': 0,  # don't break nym sending in tests
            'attrib': 2,
            'schema': 3,
            'cred_def': 4,
            'rev_reg_def': 5,
            'rev_reg_entry': 6
        }
    req = await payment.build_set_txn_fees_req(
        wallet_handle, trustee_did, libsovtoken_payment_method, json.dumps(fees)
    )
    req = await ledger.multi_sign_request(wallet_handle, trustee_did, req)
    req = await ledger.multi_sign_request(wallet_handle, trustee_did2, req)
    req = await ledger.multi_sign_request(wallet_handle, trustee_did3, req)
    res = json.loads(await ledger.submit_request(pool_handle, req))
    assert res['op'] == 'REPLY'

    # set auth rule for nym (identity owner)
    req = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', None,
                                               json.dumps({
                                                   'constraint_id': 'OR',
                                                   'auth_constraints': [
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '0',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'nym'}
                                                       },
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '2',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'nym'}
                                                       },
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '101',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'nym'}
                                                       }
                                                   ]
                                               }))
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    assert res['op'] == 'REPLY'

    # set auth rule for attrib
    req = await ledger.build_auth_rule_request(trustee_did, '100', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': '*',
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {'fees': 'attrib'}
                                               }))
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    assert res['op'] == 'REPLY'

    # set auth rule for schema
    req = await ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'OR',
                                                   'auth_constraints': [
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '0',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'schema'}
                                                       },
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '2',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'schema'}
                                                       },
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '101',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'schema'}
                                                       }
                                                   ]
                                               }))
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    assert res['op'] == 'REPLY'

    # set auth rule for cred def
    req = await ledger.build_auth_rule_request(trustee_did, '102', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'OR',
                                                   'auth_constraints': [
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '0',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'cred_def'}
                                                       },
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '2',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'cred_def'}
                                                       },
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '101',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'cred_def'}
                                                       }
                                                   ]
                                               }))
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    assert res['op'] == 'REPLY'

    # set auth rule for rev reg def
    req = await ledger.build_auth_rule_request(trustee_did, '113', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'OR',
                                                   'auth_constraints': [
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '0',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'rev_reg_def'}
                                                       },
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '2',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'rev_reg_def'}
                                                       },
                                                       {
                                                           'constraint_id': 'ROLE',
                                                           'role': '101',
                                                           'sig_count': 1,
                                                           'need_to_be_owner': False,
                                                           'metadata': {'fees': 'rev_reg_def'}
                                                       }
                                                   ]
                                               }))
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    assert res['op'] == 'REPLY'

    # set auth rule for rev reg entry
    req = await ledger.build_auth_rule_request(trustee_did, '114', 'ADD', '*', None, '*',
                                               json.dumps({
                                                   'constraint_id': 'ROLE',
                                                   'role': '*',
                                                   'sig_count': 1,
                                                   'need_to_be_owner': False,
                                                   'metadata': {'fees': 'rev_reg_entry'}
                                               }))
    res = json.loads(await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req))
    assert res['op'] == 'REPLY'

    return fees


async def add_fees_and_send_request(
        pool_handle, wallet_handle, trustee_did, address, req_without_fees, req_fee
):
    source, amount = await get_payment_sources(pool_handle, wallet_handle, address)
    req_with_fees_json, _ = await payment.add_request_fees(
        wallet_handle, trustee_did, req_without_fees, json.dumps([source]), json.dumps(
            [{'recipient': address, 'amount': amount - req_fee}]
        ), None
    )
    res = json.loads(
        await ledger.sign_and_submit_request(pool_handle, wallet_handle, trustee_did, req_with_fees_json)
    )
    assert res['op'] == 'REPLY'

    return res
