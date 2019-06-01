import pytest
from system.utils import *
from hypothesis import settings, given, strategies, Phase, Verbosity
from string import printable, ascii_letters
import hashlib
import copy
import os
import sys


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestPropertyBasedSuite:

    @pytest.mark.skip('example')
    @settings(deadline=None, max_examples=100)
    @given(var_bin=strategies.binary(5, 25).filter(lambda x: x != b'\x00\x00\x00\x00\x00'),  # <<< filter
           var_char=strategies.characters('S').filter(lambda x: x not in ['@', '#', '$']),  # <<< filter
           var_text=strategies.text(ascii_letters, min_size=10, max_size=10).map(lambda x: x.lower()),  # <<< map
           var_rec=strategies.recursive(strategies.integers() | strategies.floats(),
                                        lambda children:
                                        strategies.lists(children, min_size=3) | strategies.dictionaries(
                                            strategies.text(printable), children, min_size=3),
                                        max_leaves=10),
           var_dt_lists=
           strategies.integers(1, 5).flatmap(lambda x: strategies.lists(strategies.datetimes(), x, x)))  # <<< flatmap
    @pytest.mark.asyncio
    async def test_case_strategies(self, var_bin, var_char, var_text, var_rec, var_dt_lists):
        print()
        print(var_bin)
        print(var_char)
        print(var_text)
        print(var_rec)
        print(var_dt_lists)
        print('-'*25)

    @settings(deadline=None, max_examples=100, phases=[Phase.generate], verbosity=Verbosity.verbose)
    @given(reqid=strategies.integers(min_value=1, max_value=999999999999999),
           dest=strategies.text(ascii_letters, min_size=16, max_size=16),
           verkey=strategies.text(ascii_letters, min_size=32, max_size=32),
           alias=strategies.text(min_size=1, max_size=10000))
    @pytest.mark.asyncio
    async def test_case_nym(self, pool_handler, wallet_handler, get_default_trustee, reqid, dest, verkey, alias):
        trustee_did, trustee_vk = get_default_trustee
        roles = ['0', '2', '101', '201']
        req = {
               'protocolVersion': 2,
               'reqId': reqid,
               'identifier': trustee_did,
               'operation': {
                             'type': '1',
                             'dest': base58.b58encode(dest).decode(),
                             'verkey': base58.b58encode(verkey).decode(),
                             'role': random.choice(roles),
                             'alias': alias
                            }
                }
        res = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, json.dumps(req)))
        print(req)
        print(res)
        assert res['op'] == 'REPLY'

    @settings(deadline=None, max_examples=100)
    @given(reqid=strategies.integers(min_value=1, max_value=999999999999999),
           xhash=strategies.text().map(lambda x: hashlib.sha256(x.encode()).hexdigest()),
           key=strategies.text(printable),
           value=strategies.text(printable),
           enc=strategies.text(min_size=1))
    @pytest.mark.asyncio
    async def test_case_attrib(self, pool_handler, wallet_handler, get_default_trustee, reqid, xhash, key, value, enc):
        trustee_did, trustee_vk = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, target_did, target_vk)
        assert res['op'] == 'REPLY'
        req_base = {
                    'protocolVersion': 2,
                    'identifier': target_did,
                    'operation': {
                                  'type': '100',
                                  'dest': target_did
                                 }
                    }

        req1 = copy.deepcopy(req_base)
        req1['reqId'] = reqid + 1
        req1['operation']['hash'] = xhash
        res1 = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, json.dumps(req1)))
        print(req1)
        print(res1)
        assert res1['op'] == 'REPLY'

        req2 = copy.deepcopy(req_base)
        req2['reqId'] = reqid + 2
        req2['operation']['raw'] = json.dumps({key: value})
        res2 = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, json.dumps(req2)))
        print(req2)
        print(res2)
        assert res2['op'] == 'REPLY'

        req3 = copy.deepcopy(req_base)
        req3['reqId'] = reqid + 3
        req3['operation']['enc'] = enc
        res3 = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, json.dumps(req3)))
        print(req3)
        print(res3)
        assert res3['op'] == 'REPLY'

    @settings(deadline=None, max_examples=200)
    @given(reqid=strategies.integers(min_value=1, max_value=999999999999999),
           version=strategies.floats(min_value=0.1, max_value=999.999),
           name=strategies.text(min_size=1),
           attrs=strategies.lists(strategies.text(min_size=1), min_size=1, max_size=125))
    @pytest.mark.asyncio
    async def test_case_schema(self, pool_handler, wallet_handler, get_default_trustee, reqid, version, name, attrs):
        trustee_did, trustee_vk = get_default_trustee
        creator_did, creator_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, creator_did, creator_vk, None, 'TRUSTEE')
        assert res['op'] == 'REPLY'
        req = {
               'protocolVersion': 2,
               'reqId': reqid,
               'identifier': creator_did,
               'operation': {
                             'type': '101',
                             'data': {
                                      'version': str(version),
                                      'name': name,
                                      'attr_names': attrs
                                     }
                    }
               }
        res = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, creator_did, json.dumps(req)))
        print(req)
        print(res)
        assert res['op'] == 'REPLY'

    @settings(deadline=None, max_examples=100, verbosity=Verbosity.verbose)
    @given(reqid=strategies.integers(min_value=1, max_value=999999999999999),
           tag=strategies.text(printable, min_size=1),
           primary=strategies.recursive(
               strategies.dictionaries(
                   strategies.text(printable, min_size=1), strategies.text(printable, min_size=1),
                   min_size=1, max_size=3),
               lambda x: strategies.dictionaries(strategies.text(printable, min_size=1), x, min_size=1, max_size=3)
           ))
    @pytest.mark.asyncio
    async def test_case_cred_def(self, pool_handler, wallet_handler, get_default_trustee,
                                 reqid, tag, primary):
        trustee_did, trustee_vk = get_default_trustee
        creator_did, creator_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, creator_did, creator_vk, None, 'TRUSTEE')
        assert res['op'] == 'REPLY'
        schema_id, res = await send_schema\
            (pool_handler, wallet_handler, creator_did, random_string(10), '1.0', json.dumps(['attribute']))
        assert res['op'] == 'REPLY'
        time.sleep(1)
        res = await get_schema(pool_handler, wallet_handler, creator_did, schema_id)
        schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
        req = {
               'protocolVersion': 2,
               'reqId': reqid,
               'identifier': creator_did,
               'operation': {
                             'type': '102',
                             'ref': json.loads(schema_json)['seqNo'],
                             'signature_type': 'CL',
                             'tag': tag,
                             'data': {
                                      'primary': primary
                                     }
                            }
                }
        res = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, creator_did, json.dumps(req)))
        print(res)
        assert res['op'] == 'REPLY'
