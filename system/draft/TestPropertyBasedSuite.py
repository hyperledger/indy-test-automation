import pytest
from system.utils import *
from hypothesis import settings, given, strategies
from string import printable, ascii_letters
import hashlib
import copy


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestPropertyBasedSuite:

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

    @settings(deadline=None, max_examples=100)
    @given(reqid=strategies.integers(min_value=1),
           dest=strategies.text(ascii_letters, min_size=16, max_size=16),
           verkey=strategies.text(ascii_letters, min_size=32, max_size=32),
           alias=strategies.text(min_size=1, max_size=10000))
    @pytest.mark.asyncio
    async def test_case_nym(self, pool_handler, wallet_handler, get_default_trustee, reqid, dest, verkey, alias):
        trustee_did, trustee_vk = get_default_trustee
        roles = ['0', '2', '101', '201']
        req = {'protocolVersion': 2,
               'reqId': reqid,
               'identifier': trustee_did,
               'operation':
                   {'type': '1',
                    'dest': base58.b58encode(dest).decode(),
                    'verkey': base58.b58encode(verkey).decode(),
                    'role': random.choice(roles),
                    'alias': alias
                    }}
        res = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, json.dumps(req)))
        print(req)
        print(res)
        assert res['op'] == 'REPLY'

    @pytest.mark.asyncio
    async def test_case_attrib(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, trustee_vk = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, target_did, target_vk)
        assert res['op'] == 'REPLY'
        req_base = {'protocolVersion': 2,
                    'identifier': target_did,
                    'operation':
                        {'type': '100',
                         'dest': target_did
                         }}

        req1 = copy.deepcopy(req_base)
        req1['reqId'] = int(time.time())
        req1['operation']['hash'] = hashlib.sha256().hexdigest()
        res1 = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, json.dumps(req1)))
        print(req1)
        print(res1)
        assert res1['op'] == 'REPLY'

        req2 = copy.deepcopy(req_base)
        req2['reqId'] = int(time.time())
        req2['operation']['raw'] = '{"key": "value"}'
        res2 = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, json.dumps(req2)))
        print(req2)
        print(res2)
        assert res2['op'] == 'REPLY'

        req3 = copy.deepcopy(req_base)
        req3['reqId'] = int(time.time())
        req3['operation']['enc'] = random_string(10)
        res3 = json.loads\
            (await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, json.dumps(req3)))
        print(req3)
        print(res3)
        assert res3['op'] == 'REPLY'
