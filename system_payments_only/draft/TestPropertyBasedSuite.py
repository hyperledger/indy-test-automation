import pytest
from system.utils import *
import asyncio
from hypothesis import settings, given, strategies, Phase, Verbosity, reproduce_failure
from hypothesis.strategies import composite
from string import printable, ascii_letters
import hashlib
import copy
import os
import sys
from indy import payment, error

max_size = 1e+17


@composite
def strategy_for_op_and_data_cases(draw):
    reqid = draw(strategies.integers(min_value=1, max_value=max_size))
    reqtype = draw(strategies.integers().filter(lambda x: x not in [6, 7, 119, 20001]))
    data = draw(
        strategies.recursive(
            strategies.dictionaries(
                strategies.text(printable, min_size=1), strategies.text(printable, min_size=1), min_size=1, max_size=3
            ), lambda x: strategies.dictionaries(strategies.text(printable, min_size=1), x, min_size=1, max_size=3)
        )
    )
    return reqid, reqtype, data


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestPropertyBasedSuite:

    @pytest.mark.skip('example')
    @settings(deadline=None, max_examples=100)
    @given(var_bin=strategies.binary(5, 25).filter(lambda x: x != b'\x00\x00\x00\x00\x00'),
           var_char=strategies.characters('S').filter(lambda x: x not in ['@', '#', '$']),
           var_text=strategies.text(
               ascii_letters, min_size=10, max_size=10
           ).map(lambda x: x.lower()),  # <<< map
           var_rec=strategies.recursive(
               strategies.integers()
               | strategies.floats(),
               lambda children:
               strategies.lists(children, min_size=3)
               | strategies.dictionaries(strategies.text(printable), children, min_size=3),
               max_leaves=10
           ),
           var_dt_lists=strategies.integers(1, 5).flatmap(lambda x: strategies.lists(strategies.datetimes(), x, x)))
    @pytest.mark.asyncio
    async def test_case_strategies(self, var_bin, var_char, var_text, var_rec, var_dt_lists):
        print()
        print(var_bin)
        print(var_char)
        print(var_text)
        print(var_rec)
        print(var_dt_lists)
        print('-'*25)

    # bad behaviour with verkey field - hypothesis resend txns with the same verkey that cause rejects
    @settings(deadline=None, max_examples=250, verbosity=Verbosity.debug)
    @given(reqid=strategies.integers(min_value=1, max_value=max_size),
           dest=strategies.text(ascii_letters, min_size=16, max_size=16),
           alias=strategies.text(min_size=1, max_size=10000))
    @pytest.mark.asyncio
    async def test_case_nym(
            self, pool_handler, wallet_handler, get_default_trustee, reqid, dest, alias
    ):
        trustee_did, trustee_vk = get_default_trustee
        req = {
               'protocolVersion': 2,
               'reqId': reqid,
               'identifier': trustee_did,
               'operation': {
                             'type': '1',
                             'dest': base58.b58encode(dest).decode(),
                             'role': '201',
                             'alias': alias
                            }
                }
        print(req)
        res = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, json.dumps(req))
        )
        print(res)
        assert res['op'] == 'REPLY'

    @settings(deadline=None, max_examples=100)
    @given(reqid=strategies.integers(min_value=1, max_value=max_size),
           xhash=strategies.text().map(lambda x: hashlib.sha256(x.encode()).hexdigest()),
           key=strategies.text(min_size=1, alphabet=printable),
           value=strategies.text(min_size=1, alphabet=printable),
           enc=strategies.text(min_size=1))
    @pytest.mark.asyncio
    async def test_case_attrib(
            self, pool_handler, wallet_handler, get_default_trustee, reqid, xhash, key, value, enc
    ):
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
        res1 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, json.dumps(req1))
        )
        print(req1)
        print(res1)
        assert res1['op'] == 'REPLY'

        req2 = copy.deepcopy(req_base)
        req2['reqId'] = reqid + 2
        req2['operation']['raw'] = json.dumps({key: value})
        res2 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, json.dumps(req2))
        )
        print(req2)
        print(res2)
        assert res2['op'] == 'REPLY'

        req3 = copy.deepcopy(req_base)
        req3['reqId'] = reqid + 3
        req3['operation']['enc'] = enc
        res3 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, json.dumps(req3))
        )
        print(req3)
        print(res3)
        assert res3['op'] == 'REPLY'

    @settings(deadline=None, max_examples=250)
    @given(reqid=strategies.integers(min_value=1, max_value=max_size),
           version=strategies.floats(min_value=0.1, max_value=999.999),
           name=strategies.text(min_size=1),
           attrs=strategies.lists(strategies.text(min_size=1), min_size=1, max_size=125))
    @pytest.mark.asyncio
    async def test_case_schema(
            self, pool_handler, wallet_handler, get_default_trustee, reqid, version, name, attrs
    ):
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
        res = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, creator_did, json.dumps(req))
        )
        print(req)
        print(res)
        assert res['op'] == 'REPLY'

    @settings(deadline=None, max_examples=250, verbosity=Verbosity.verbose)
    @given(reqid=strategies.integers(min_value=1, max_value=max_size),
           tag=strategies.text(printable, min_size=1),
           primary=strategies.recursive(
               strategies.dictionaries(
                   strategies.text(printable, min_size=1), strategies.text(printable, min_size=1),
                   min_size=1, max_size=3),
               lambda x: strategies.dictionaries(strategies.text(printable, min_size=1), x, min_size=1, max_size=3)
           ))
    @pytest.mark.asyncio
    async def test_case_cred_def(
            self, pool_handler, wallet_handler, get_default_trustee, reqid, tag, primary
    ):
        trustee_did, trustee_vk = get_default_trustee
        creator_did, creator_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, creator_did, creator_vk, None, 'TRUSTEE')
        assert res['op'] == 'REPLY'
        schema_id, res = await send_schema(
            pool_handler, wallet_handler, creator_did, random_string(10), '1.0', json.dumps(['attribute'])
        )
        assert res['op'] == 'REPLY'
        res = await ensure_get_something(get_schema, pool_handler, wallet_handler, creator_did, schema_id)
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
        res = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, creator_did, json.dumps(req))
        )
        print(req)
        print(res)
        assert res['op'] == 'REPLY'

    @settings(deadline=None, max_examples=10000, verbosity=Verbosity.verbose)
    @given(values=strategy_for_op_and_data_cases())
    @pytest.mark.asyncio
    async def test_case_random_req_op(
            self, pool_handler, wallet_handler, get_default_trustee, values
    ):
        trustee_did, trustee_vk = get_default_trustee
        req = {
            'protocolVersion': 2,
            'reqId': values[0],
            'identifier': trustee_did,
            'operation': values[2]
        }
        # client-side validation
        with pytest.raises(IndyError):
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, json.dumps(req))

    @settings(deadline=None, max_examples=10000, verbosity=Verbosity.verbose)
    @given(values=strategy_for_op_and_data_cases())
    @pytest.mark.asyncio
    async def test_case_random_req_data(
            self, pool_handler, wallet_handler, get_default_trustee, values
    ):
        trustee_did, trustee_vk = get_default_trustee
        req = {
            'protocolVersion': 2,
            'reqId': values[0],
            'identifier': trustee_did,
            'operation': {
                'type': str(values[1]),
                'data': values[2]
            }
        }
        res = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, json.dumps(req))
        )
        # server-side static validation
        try:
            assert res['op'] == 'REQNACK'
        except KeyError:
            res = {k: json.loads(v) for k, v in res.items()}
            assert all([v['op'] == 'REQNACK' for k, v in res.items()])

    @settings(deadline=None, max_examples=10000, verbosity=Verbosity.verbose)
    @given(amount=strategies.integers(min_value=0, max_value=max_size),
           seqno=strategies.integers(min_value=0, max_value=max_size),
           signatures=strategies.text(ascii_letters, min_size=0, max_size=max_size),
           reqid=strategies.integers(min_value=1, max_value=max_size))
    @pytest.mark.asyncio
    async def test_case_invalid_payment(
            self, payment_init, pool_handler, wallet_handler, get_default_trustee, amount, seqno, signatures, reqid
    ):
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        try:
            address1 = await payment.create_payment_address(
                wallet_handler, libsovtoken_payment_method, json.dumps({'seed': '0000000000000000000000000Wallet1'})
            )
            address2 = await payment.create_payment_address(
                wallet_handler, libsovtoken_payment_method, json.dumps({'seed': '0000000000000000000000000Wallet2'})
            )
        except IndyError:
            address1 = 'pay:sov:aRczGoccsHV7mNJgpBVYwCveytvyL8JBa1X28GFSwD44m76eE'
            address2 = 'pay:sov:H8v7bJwwKEnEUjd5dGec3oTbLMwgFLUVHL7kDKtVqBtLaQ2JG'
        req = {
            'operation':
                {'type': '10001',
                 'outputs': [
                     {'address': address2.split(':')[-1],
                      'amount': amount}
                 ],
                 'inputs': [
                     {'address': address1.split(':')[-1],
                      'seqNo': seqno}
                 ],
                 'signatures':
                     [signatures]},
            'reqId': reqid,
            'protocolVersion': 2,
            'identifier': trustee_did
        }
        print(req)
        res = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, json.dumps(req))
        )
        print(res)
        assert res['op'] == 'REQNACK'
