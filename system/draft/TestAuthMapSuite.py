import pytest
import asyncio
from system.utils import *
from random import randrange as rr
import hashlib
import time
from datetime import datetime, timedelta, timezone
from indy import payment


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestAuthMapSuite:

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.asyncio
    async def test_case_nym(self, pool_handler, wallet_handler, get_default_trustee,
                            adder_role, adder_role_num, editor_role, editor_role_num):
        trustee_did, _ = get_default_trustee
        new_did, new_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        # add adder to add nym
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        # add editor to edit nym
        editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['op'] == 'REPLY'
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'verkey', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        # add nym with verkey by adder
        res4 = await send_nym(pool_handler, wallet_handler, adder_did, new_did, adder_vk)  # push adder vk
        print(res4)
        assert res4['op'] == 'REPLY'
        # edit verkey by editor
        res5 = await send_nym(pool_handler, wallet_handler, editor_did, new_did, editor_vk)  # push editor vk
        print(res5)
        assert res5['op'] == 'REPLY'
        # negative cases
        if adder_role != editor_role:
            # try to add another nym with editor did - should be rejected
            res6 = await send_nym(pool_handler, wallet_handler, editor_did, random_did_and_json()[0])
            print(res6)
            assert res6['op'] == 'REJECT'
            # try to edit initial nym one more time with adder did - should be rejected
            res7 = await send_nym(pool_handler, wallet_handler, adder_did, new_did, adder_vk)
            print(res7)
            assert res7['op'] == 'REJECT'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.asyncio
    async def test_case_attrib(self, pool_handler, wallet_handler, get_default_trustee,
                               adder_role, adder_role_num, editor_role, editor_role_num):
        trustee_did, _ = get_default_trustee
        # add target nym
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, target_did, target_vk)
        assert res['op'] == 'REPLY'
        # add adder to add attrib
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        # add editor to edit attrib
        editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['op'] == 'REPLY'
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '100', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        # set rule for editing
        req = await ledger.build_auth_rule_request(trustee_did, '100', 'EDIT', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        # add attrib for target did by non-owner adder
        res4 = await send_attrib(pool_handler, wallet_handler, adder_did, target_did,
                                 None, json.dumps({'key1': 'value1'}), None)
        print(res4)
        assert res4['op'] == 'REPLY'
        # edit attrib for target did by non-owner editor
        res5 = await send_attrib(pool_handler, wallet_handler, editor_did, target_did,
                                 None, json.dumps({'key1': 'value2'}), None)
        print(res5)
        assert res5['op'] == 'REPLY'
        # negative cases
        if adder_role != editor_role:
            # try to add another attrib with editor did - should be rejected
            res6 = await send_attrib(pool_handler, wallet_handler, editor_did, target_did,
                                     None, json.dumps({'key2': 'value1'}), None)
            print(res6)
            assert res6['op'] == 'REJECT'
            # try to edit initial attrib one more time with adder did - should be rejected
            res7 = await send_attrib(pool_handler, wallet_handler, adder_did, target_did,
                                     None, json.dumps({'key1': 'value3'}), None)
            print(res7)
            assert res7['op'] == 'REJECT'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.asyncio
    async def test_case_schema(self, pool_handler, wallet_handler, get_default_trustee,
                               adder_role, adder_role_num):  # we can add schema only
        trustee_did, _ = get_default_trustee
        # add adder to add schema
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        # add schema
        res4 = await send_schema(pool_handler, wallet_handler, adder_did, 'schema1', '1.0', json.dumps(['attr1']))
        print(res4)
        assert res4[1]['op'] == 'REPLY'
        # edit schema - nobody can edit schemas - should be rejected
        res5 = await send_schema(pool_handler, wallet_handler, adder_did, 'schema1', '1.0',
                                 json.dumps(['attr1', 'attr2']))
        print(res5)
        assert res5[1]['op'] == 'REJECT'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.asyncio
    # use the same did with different roles to ADD and EDIT since adder did is a part of unique cred def id
    async def test_case_cred_def(self, pool_handler, wallet_handler, get_default_trustee,
                                 adder_role, adder_role_num, editor_role, editor_role_num):
        trustee_did, _ = get_default_trustee
        # add adder to add cred def
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        schema_id, _ = await send_schema(pool_handler, wallet_handler, trustee_did,
                                         'schema1', '1.0', json.dumps(["age", "sex", "height", "name"]))
        await asyncio.sleep(1)
        res = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
        schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '102', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        # set rule for editing
        req = await ledger.build_auth_rule_request(trustee_did, '102', 'EDIT', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        # add cred def
        cred_def_id, cred_def_json = \
            await anoncreds.issuer_create_and_store_credential_def(wallet_handler, adder_did, schema_json, 'TAG1',
                                                                   None, json.dumps({'support_revocation': False}))
        request = await ledger.build_cred_def_request(adder_did, cred_def_json)
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, request))
        print(res4)
        assert res4['op'] == 'REPLY'
        if adder_role != editor_role:
            # try to edit cred def as adder - should be rejected
            _request = json.loads(request)
            _request['operation']['data']['primary']['n'] = '123456789'
            _request['reqId'] += _request['reqId']
            res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did,
                                                                   json.dumps(_request)))
            print(res5)
            assert res5['op'] == 'REJECT'
            # change adder role to edit cred def
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, None, None, editor_role)
            print(res)
            assert res['op'] == 'REPLY'
        # edit cred def
        request = json.loads(request)
        request['operation']['data']['primary']['n'] = '123456'
        request['reqId'] += request['reqId']
        res6 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did,
                                                               json.dumps(request)))
        print(res6)
        assert res6['op'] == 'REPLY'
        if adder_role != editor_role:
            # try to add another cred def as editor - should be rejected
            cred_def_id, cred_def_json = \
                await anoncreds.issuer_create_and_store_credential_def(wallet_handler, adder_did, schema_json, 'TAG2',
                                                                       None, json.dumps({'support_revocation': True}))
            request = await ledger.build_cred_def_request(adder_did, cred_def_json)
            res7 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, request))
            print(res7)
            assert res7['op'] == 'REJECT'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.asyncio
    # use the same did with different roles to ADD and EDIT since adder did is a part of unique revoc reg def id
    async def test_case_revoc_reg_def(self, pool_handler, wallet_handler, get_default_trustee,
                                      adder_role, adder_role_num, editor_role, editor_role_num):
        trustee_did, _ = get_default_trustee
        # add adder to add revoc reg def
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        schema_id, _ = await send_schema(pool_handler, wallet_handler, trustee_did,
                                         'schema1', '1.0', json.dumps(['age', 'sex', 'height', 'name']))
        await asyncio.sleep(1)
        res = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
        schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
        cred_def_id, _, res = await send_cred_def(pool_handler, wallet_handler, trustee_did, schema_json,
                                                  'cred_def_tag', None, json.dumps({'support_revocation': True}))
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '113', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        # set rule for editing
        req = await ledger.build_auth_rule_request(trustee_did, '113', 'EDIT', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        # add revoc reg def
        tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
        tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
        revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = \
            await anoncreds.issuer_create_and_store_revoc_reg(wallet_handler, adder_did, None, 'TAG1',
                                                              cred_def_id, json.dumps({
                                                                'max_cred_num': 1,
                                                                'issuance_type': 'ISSUANCE_BY_DEFAULT'}),
                                                              tails_writer_handle)
        request = await ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, request))
        print(res4)
        assert res4['op'] == 'REPLY'
        if adder_role != editor_role:
            # try to edit revoc reg def as adder - should be rejected
            _request = json.loads(request)
            _request['operation']['value']['tailsHash'] = random_string(30)
            _request['reqId'] += _request['reqId']
            res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did,
                                                                   json.dumps(_request)))
            print(res5)
            assert res5['op'] == 'REJECT'
            # change adder role to edit revoc reg def
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, None, None, editor_role)
            print(res)
            assert res['op'] == 'REPLY'
        # edit revoc reg def
        request = json.loads(request)
        request['operation']['value']['tailsHash'] = random_string(20)
        request['reqId'] += request['reqId']
        res6 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did,
                                                               json.dumps(request)))
        print(res6)
        assert res6['op'] == 'REPLY'
        if adder_role != editor_role:
            # try to add another revoc reg def as editor - should be rejected
            revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = \
                await anoncreds.issuer_create_and_store_revoc_reg(wallet_handler, adder_did, None, 'TAG2',
                                                                  cred_def_id, json.dumps({
                                                                      'max_cred_num': 2,
                                                                      'issuance_type': 'ISSUANCE_BY_DEFAULT'}),
                                                                  tails_writer_handle)
            request = await ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
            res7 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, request))
            print(res7)
            assert res7['op'] == 'REJECT'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.asyncio
    async def test_case_revoc_reg_entry(self, pool_handler, wallet_handler, get_default_trustee,
                                        adder_role, adder_role_num, editor_role, editor_role_num):
        trustee_did, _ = get_default_trustee
        # add adder to add revoc reg entry
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        schema_id, _ = await send_schema(pool_handler, wallet_handler, trustee_did,
                                         'schema1', '1.0', json.dumps(['age', 'sex', 'height', 'name']))
        await asyncio.sleep(1)
        res = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
        schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
        cred_def_id, _, res = await send_cred_def(pool_handler, wallet_handler, trustee_did, schema_json,
                                                  'cred_def_tag', None, json.dumps({'support_revocation': True}))
        # set rule for revoc reg def adding - network monitor case
        req = await ledger.build_auth_rule_request(trustee_did, '113', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '*',
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res21 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res21)
        assert res21['op'] == 'REPLY'
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '114', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res22 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res22)
        assert res22['op'] == 'REPLY'
        # set rule for editing
        req = await ledger.build_auth_rule_request(trustee_did, '114', 'EDIT', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        # add revoc reg entry
        tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
        tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
        revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = \
            await anoncreds.issuer_create_and_store_revoc_reg(wallet_handler, adder_did, None, 'TAG1',
                                                              cred_def_id, json.dumps({
                                                                'max_cred_num': 10,
                                                                'issuance_type': 'ISSUANCE_BY_DEFAULT'}),
                                                              tails_writer_handle)
        req = await ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
        assert res['op'] == 'REPLY'
        request = await ledger.build_revoc_reg_entry_request(adder_did, revoc_reg_def_id, 'CL_ACCUM',
                                                             revoc_reg_entry_json)
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, request))
        print(res4)
        assert res4['op'] == 'REPLY'
        if adder_role != editor_role:
            # try to edit revoc reg entry as adder - should be rejected
            _request = json.loads(request)
            _request['operation']['value']['prevAccum'] = _request['operation']['value']['accum']
            _request['operation']['value']['accum'] = random_string(20)
            _request['operation']['value']['revoked'] = [7, 8, 9]
            _request['reqId'] += _request['reqId']
            res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did,
                                                                   json.dumps(_request)))
            print(res5)
            assert res5['op'] == 'REJECT'
            # change adder role to edit revoc reg def
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, None, None, editor_role)
            print(res)
            assert res['op'] == 'REPLY'
        # edit revoc reg entry
        request = json.loads(request)
        request['operation']['value']['prevAccum'] = request['operation']['value']['accum']
        request['operation']['value']['accum'] = random_string(10)
        request['operation']['value']['revoked'] = [1, 2, 3]
        request['reqId'] += request['reqId']
        res6 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did,
                                                               json.dumps(request)))
        print(res6)
        assert res6['op'] == 'REPLY'
        if adder_role != editor_role:
            # try to add another revoc reg entry as editor - should be rejected
            revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = \
                await anoncreds.issuer_create_and_store_revoc_reg(wallet_handler, adder_did, None, 'TAG2',
                                                                  cred_def_id, json.dumps({
                                                                        'max_cred_num': 20,
                                                                        'issuance_type': 'ISSUANCE_BY_DEFAULT'}),
                                                                  tails_writer_handle)
            req = await ledger.build_revoc_reg_def_request(adder_did, revoc_reg_def_json)
            res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
            assert res['op'] == 'REPLY'
            request = await ledger.build_revoc_reg_entry_request(adder_did, revoc_reg_def_id, 'CL_ACCUM',
                                                                 revoc_reg_entry_json)
            res7 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, request))
            print(res7)
            assert res7['op'] == 'REJECT'

    @pytest.mark.skip('INDY-2024')
    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.asyncio
    async def test_case_node(self, pool_handler, wallet_handler, get_default_trustee,
                             adder_role, adder_role_num, editor_role, editor_role_num):
        trustee_did, _ = get_default_trustee
        # add adder to add node
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        # add editor to edit node
        editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['op'] == 'REPLY'
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '0', 'ADD', 'services', '*', str(['VALIDATOR']),
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        # set rule for editing
        req = await ledger.build_auth_rule_request(trustee_did, '0', 'EDIT', 'services', str(['VALIDATOR']), str([]),
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        # add node
        alias = random_string(5)
        client_ip = '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255))
        client_port = rr(1, 32767)
        node_ip = '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255))
        node_port = rr(1, 32767)
        req = await ledger.build_node_request(adder_did, adder_vk,  # adder_vk is used as node target did here
                                              json.dumps(
                                                   {
                                                       'alias': alias,
                                                       'client_ip': client_ip,
                                                       'client_port': client_port,
                                                       'node_ip': node_ip,
                                                       'node_port': node_port,
                                                       'services': ['VALIDATOR']
                                                   }))
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
        print(res4)
        assert res4['op'] == 'REPLY'
        # edit node
        req = await ledger.build_node_request(editor_did, adder_vk,  # adder_vk is used as node target did here
                                              json.dumps(
                                                   {
                                                       'alias': alias,
                                                       'services': []
                                                   }))
        res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, editor_did, req))
        print(res5)
        assert res5['op'] == 'REPLY'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.asyncio
    async def test_case_pool_upgrade(self, pool_handler, wallet_handler, get_default_trustee,
                                     adder_role, adder_role_num, editor_role, editor_role_num):
        trustee_did, _ = get_default_trustee
        # add adder to start pool upgrdae
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        # add editor to cancel pool upgrade
        editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['op'] == 'REPLY'
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '109', 'ADD', 'action', '*', 'start',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        # set rule for editing
        req = await ledger.build_auth_rule_request(trustee_did, '109', 'EDIT', 'action', 'start', 'cancel',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        # start pool upgrade
        init_time = 30
        version = '1.9.999'
        name = 'upgrade' + '_' + version + '_' + datetime.now(tz=timezone.utc).strftime('%Y-%m-%dT%H:%M:%S%z')
        _sha256 = hashlib.sha256().hexdigest()
        _timeout = 5
        reinstall = False
        force = False
        package = 'indy-node'
        dests = ['Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv', '8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb',
                 'DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya', '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA',
                 '4SWokCJWJc69Tn74VvLS6t2G2ucvXqM9FDMsWJjmsUxe', 'Cv1Ehj43DDM5ttNBmC6VPpEfwXWwfGktHwjDJsTV5Fz8',
                 'BM8dTooz5uykCbYSAAFwKNkYfT4koomBHsSWHTDtkjhW']
        docker_7_schedule = json.dumps(dict(
            {dest: datetime.strftime(datetime.now(tz=timezone.utc) + timedelta(minutes=init_time + i * 5),
                                     '%Y-%m-%dT%H:%M:%S%z')
             for dest, i in zip(dests, range(len(dests)))}
        ))
        req = await ledger.build_pool_upgrade_request(adder_did, name, version, 'start', _sha256, _timeout,
                                                      docker_7_schedule, None, reinstall, force, package)
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
        print(res4)
        assert res4['op'] == 'REPLY'
        # cancel pool upgrade
        req = await ledger.build_pool_upgrade_request(editor_did, name, version, 'cancel', _sha256, _timeout,
                                                      docker_7_schedule, None, reinstall, force, package)
        res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, editor_did, req))
        print(res5)
        assert res5['op'] == 'REPLY'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.asyncio
    async def test_case_pool_restart(self, pool_handler, wallet_handler, get_default_trustee,
                                     adder_role, adder_role_num):  # we can add pool restart only
        trustee_did, _ = get_default_trustee
        # add adder to restart pool
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        await asyncio.sleep(15)
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '118', 'ADD', 'action', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        # restart pool
        req = await ledger.build_pool_restart_request\
            (adder_did, 'start', datetime.strftime(datetime.now(tz=timezone.utc) + timedelta(minutes=60),
                                                   '%Y-%m-%dT%H:%M:%S%z'))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
        res3 = [json.loads(v) for k, v in res3.items()]
        print(res3)
        assert all([res['op'] == 'REPLY' for res in res3])

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.asyncio
    async def test_case_validator_info(self, pool_handler, wallet_handler, get_default_trustee,
                                       adder_role, adder_role_num):  # we can add validator info only
        trustee_did, _ = get_default_trustee
        # add adder to get validator info
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        await asyncio.sleep(15)
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '119', 'ADD', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        req = await ledger.build_get_validator_info_request(adder_did)
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
        res3 = [json.loads(v) for k, v in res3.items()]
        print(res3)
        assert all([res['op'] == 'REPLY' for res in res3])

    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.asyncio
    async def test_case_pool_config(self, pool_handler, wallet_handler, get_default_trustee,
                                    editor_role, editor_role_num):  # we can edit pool config only
        trustee_did, _ = get_default_trustee
        # add editor to edit pool config
        editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['op'] == 'REPLY'
        # set rule for editing
        req = await ledger.build_auth_rule_request(trustee_did, '111', 'EDIT', 'action', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        req = await ledger.build_pool_config_request(editor_did, False, False)
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, editor_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'

    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.asyncio
    async def test_case_auth_rule(self, pool_handler, wallet_handler, get_default_trustee,
                                  editor_role, editor_role_num):  # we can edit auth rule only
        trustee_did, _ = get_default_trustee
        # add editor to edit auth rule
        editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['op'] == 'REPLY'
        # set rule for editing
        req = await ledger.build_auth_rule_request(trustee_did, '120', 'EDIT', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        await asyncio.sleep(15)
        req = await ledger.build_auth_rule_request(editor_did, '111', 'EDIT', 'action', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '*',
                                                       'sig_count': 5,
                                                       'need_to_be_owner': True,
                                                       'metadata': {}
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, editor_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.parametrize('sig_count', [0, 1, 3])
    @pytest.mark.asyncio
    async def test_case_mint(self, pool_handler, wallet_handler, get_default_trustee,
                             adder_role, adder_role_num, sig_count):
        await payment_initializer('libsovtoken.so', 'sovtoken_init')
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        address = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps(
            {"seed": str('0000000000000000000000000Wallet0')}))
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '10000', 'ADD', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': sig_count,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        if sig_count == 0:
            # add identity owner adder to mint tokens
            adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, None)
            assert res['op'] == 'REPLY'
            req, _ = await payment.build_mint_req(wallet_handler, adder_did,
                                                  json.dumps([{"recipient": address, "amount": 100}]), None)
            res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
            print(res1)
            assert res1['op'] == 'REPLY'
        elif sig_count == 1:
            # add adder to mint tokens
            adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
            assert res['op'] == 'REPLY'
            req, _ = await payment.build_mint_req(wallet_handler, adder_did,
                                                  json.dumps([{"recipient": address, "amount": 100}]), None)
            res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
            print(res1)
            assert res1['op'] == 'REPLY'
        else:
            # add adders to mint tokens
            adder_did1, adder_vk1 = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did1, adder_vk1, None, adder_role)
            assert res['op'] == 'REPLY'
            adder_did2, adder_vk2 = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did2, adder_vk2, None, adder_role)
            assert res['op'] == 'REPLY'
            adder_did3, adder_vk3 = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did3, adder_vk3, None, adder_role)
            assert res['op'] == 'REPLY'
            req, _ = await payment.build_mint_req(wallet_handler, adder_did1,
                                                  json.dumps([{"recipient": address, "amount": 100}]), None)
            req = await ledger.multi_sign_request(wallet_handler, adder_did1, req)
            req = await ledger.multi_sign_request(wallet_handler, adder_did2, req)
            req = await ledger.multi_sign_request(wallet_handler, adder_did3, req)
            res1 = json.loads(await ledger.submit_request(pool_handler, req))
            print(res1)
            assert res1['op'] == 'REPLY'

    @pytest.mark.parametrize('editor_role, editor_role_num', [
        ('NETWORK_MONITOR', '201'),
        ('TRUST_ANCHOR', '101'),
        ('STEWARD', '2'),
        ('TRUSTEE', '0')
    ])
    @pytest.mark.parametrize('sig_count', [0, 1, 3])
    @pytest.mark.asyncio
    async def test_case_set_fees(self, pool_handler, wallet_handler, get_default_trustee,
                                 editor_role, editor_role_num, sig_count):
        await payment_initializer('libsovtoken.so', 'sovtoken_init')
        libsovtoken_payment_method = 'sov'
        fees = {'1': 1, '100': 1, '101': 1, '102': 1, '113': 1, '114': 1, '10001': 1}
        trustee_did, _ = get_default_trustee
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '20000', 'EDIT', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': sig_count,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        if sig_count == 0:
            # add identity owner editor to set fees
            editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, None)
            assert res['op'] == 'REPLY'
            req = await payment.build_set_txn_fees_req(wallet_handler, editor_did, libsovtoken_payment_method,
                                                       json.dumps(fees))
            res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, editor_did, req))
            print(res1)
            assert res1['op'] == 'REPLY'
        elif sig_count == 1:
            # add editor to set fees
            editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
            assert res['op'] == 'REPLY'
            req = await payment.build_set_txn_fees_req(wallet_handler, editor_did, libsovtoken_payment_method,
                                                       json.dumps(fees))
            res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, editor_did, req))
            print(res1)
            assert res1['op'] == 'REPLY'
        else:
            # add editors to set fees
            editor_did1, editor_vk1 = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did1, editor_vk1, None, editor_role)
            assert res['op'] == 'REPLY'
            editor_did2, editor_vk2 = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did2, editor_vk2, None, editor_role)
            assert res['op'] == 'REPLY'
            editor_did3, editor_vk3 = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did3, editor_vk3, None, editor_role)
            assert res['op'] == 'REPLY'
            req = await payment.build_set_txn_fees_req(wallet_handler, editor_did1, libsovtoken_payment_method,
                                                       json.dumps(fees))
            req = await ledger.multi_sign_request(wallet_handler, editor_did1, req)
            req = await ledger.multi_sign_request(wallet_handler, editor_did2, req)
            req = await ledger.multi_sign_request(wallet_handler, editor_did3, req)
            res1 = json.loads(await ledger.submit_request(pool_handler, req))
            print(res1)
            assert res1['op'] == 'REPLY'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.parametrize('sig_count', [0, 1, 3])
    @pytest.mark.asyncio
    async def test_case_payment(self, pool_handler, wallet_handler, get_default_trustee,
                                adder_role, adder_role_num, sig_count):
        await payment_initializer('libsovtoken.so', 'sovtoken_init')
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        address1 = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps(
            {"seed": str('0000000000000000000000000Wallet1')}))
        address2 = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps(
            {"seed": str('0000000000000000000000000Wallet2')}))
        # set rule for easier mint adding
        req = await ledger.build_auth_rule_request(trustee_did, '10000', 'ADD', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '*',
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res1)
        assert res1['op'] == 'REPLY'
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '10001', 'ADD', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': sig_count,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        # initial minting
        req, _ = await payment.build_mint_req(wallet_handler, trustee_did,
                                              json.dumps([{"recipient": address1, "amount": 100}]), None)
        res11 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res11)
        assert res11['op'] == 'REPLY'
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address1)
        res111 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        source1 = \
            json.loads(await payment.parse_get_payment_sources_response(libsovtoken_payment_method,
                                                                        res111))[0]['source']
        if sig_count == 0:
            # add identity owner adder to send xfer
            adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, None)
            assert res['op'] == 'REPLY'
            req, _ = await payment.build_payment_req(wallet_handler, adder_did,
                                                     json.dumps([source1]),
                                                     json.dumps([{"recipient": address2, "amount": 100}]), None)
            res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
            print(res1)
            assert res1['op'] == 'REPLY'
        elif sig_count == 1:
            # add adder to send xfer
            adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
            assert res['op'] == 'REPLY'
            req, _ = await payment.build_payment_req(wallet_handler, adder_did,
                                                     json.dumps([source1]),
                                                     json.dumps([{"recipient": address2, "amount": 100}]), None)
            res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req))
            print(res1)
            assert res1['op'] == 'REPLY'
        else:
            # add adders to send xfer
            adder_did1, adder_vk1 = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did1, adder_vk1, None, adder_role)
            assert res['op'] == 'REPLY'
            adder_did2, adder_vk2 = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did2, adder_vk2, None, adder_role)
            assert res['op'] == 'REPLY'
            adder_did3, adder_vk3 = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did3, adder_vk3, None, adder_role)
            assert res['op'] == 'REPLY'
            req, _ = await payment.build_payment_req(wallet_handler, adder_did1,
                                                     json.dumps([source1]),
                                                     json.dumps([{"recipient": address2, "amount": 100}]), None)
            req = await ledger.multi_sign_request(wallet_handler, adder_did1, req)
            req = await ledger.multi_sign_request(wallet_handler, adder_did2, req)
            req = await ledger.multi_sign_request(wallet_handler, adder_did3, req)
            res1 = json.loads(await ledger.submit_request(pool_handler, req))
            print(res1)
            assert res1['op'] == 'REPLY'
