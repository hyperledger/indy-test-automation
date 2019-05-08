import pytest
from system.utils import *


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
                                 None, json.dumps({'key': 'value1'}), None)
        print(res4)
        assert res4['op'] == 'REPLY'
        # edit attrib for target did by non-owner editor
        res5 = await send_attrib(pool_handler, wallet_handler, editor_did, target_did,
                                 None, json.dumps({'key': 'value2'}), None)
        print(res5)
        assert res5['op'] == 'REPLY'

    @pytest.mark.parametrize('adder_role, adder_role_num', [
        ('TRUSTEE', '0'),
        ('STEWARD', '2'),
        ('TRUST_ANCHOR', '101'),
        ('NETWORK_MONITOR', '201')
    ])
    @pytest.mark.asyncio
    async def test_case_schema(self, pool_handler, wallet_handler, get_default_trustee,
                               adder_role, adder_role_num):
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
        time.sleep(1)
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
            await anoncreds.issuer_create_and_store_credential_def(wallet_handler, adder_did, schema_json, 'TAG',
                                                                   None, json.dumps({'support_revocation': False}))
        request = await ledger.build_cred_def_request(adder_did, cred_def_json)
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, request))
        print(res4)
        assert res4['op'] == 'REPLY'
        if adder_role != editor_role:
            # change adder role to edit cred def
            res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, None, None, editor_role)
            print(res)
            assert res['op'] == 'REPLY'
        # edit cred def
        request = json.loads(request)
        request['operation']['data']['primary']['n'] = '123456'
        request['reqId'] += request['reqId']
        res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did,
                                                               json.dumps(request)))
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
    # use the same did with different roles to ADD and EDIT since adder did is a part of unique revoc reg def id
    async def test_case_revoc_reg_def(self, pool_handler, wallet_handler, get_default_trustee,
                                      adder_role, adder_role_num, editor_role, editor_role_num):
        trustee_did, _ = get_default_trustee
        # add adder to add revoc reg def
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res01 = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res01['op'] == 'REPLY'
        # add editor to edit revoc reg def
        editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res02 = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res02['op'] == 'REPLY'
        schema_id, _ = await send_schema(pool_handler, wallet_handler, trustee_did,
                                         'schema1', '1.0', json.dumps(['age', 'sex', 'height', 'name']))
        time.sleep(1)
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
        revoc_reg_def_id, _, _, res4 = await send_revoc_reg_def(pool_handler, wallet_handler, adder_did, None,
                                                                'TAG', cred_def_id,
                                                                json.dumps({'max_cred_num': 1,
                                                                            'issuance_type': 'ISSUANCE_BY_DEFAULT'}))
        print(res4)
        assert res4['op'] == 'REPLY'
        # edit revoc reg def
        revoc_reg_def_id, _, _, res5 = await send_revoc_reg_def(pool_handler, wallet_handler, editor_did, None,
                                                                'TAG', cred_def_id,
                                                                json.dumps({'max_cred_num': 2,
                                                                            'issuance_type': 'ISSUANCE_BY_DEMAND'}))
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
    async def test_case_revoc_reg_entry(self, pool_handler, wallet_handler, get_default_trustee,
                                        adder_role, adder_role_num, editor_role, editor_role_num):
        trustee_did, _ = get_default_trustee
        # add adder to add revoc reg entry
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['op'] == 'REPLY'
        # add editor to edit revoc reg entry
        editor_did, editor_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['op'] == 'REPLY'
