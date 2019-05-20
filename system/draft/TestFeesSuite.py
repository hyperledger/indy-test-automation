import pytest
from system.utils import *
from indy import payment


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestFeesSuite:

    @pytest.mark.parametrize('schema_adder_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
    @pytest.mark.parametrize('cred_def_adder_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
    @pytest.mark.asyncio
    async def test_case_schema_cred_def_rrd_rre_production(self, pool_handler, wallet_handler, get_default_trustee,
                                                           schema_adder_role, cred_def_adder_role):
        await payment_initializer('libsovtoken.so', 'sovtoken_init')
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')

        # add adder to add schema
        adder_did, adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, schema_adder_role)
        print(res)
        assert res['op'] == 'REPLY'

        # add adder to add cred_def
        cd_adder_did, cd_adder_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym\
            (pool_handler, wallet_handler, trustee_did, cd_adder_did, cd_adder_vk, None, cred_def_adder_role)
        print(res)
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
                                                               'metadata': {'fees': '101'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '2',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': '101'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': '101'}
                                                           }
                                                       ]
                                                   }))
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res1)
        assert res1['op'] == 'REPLY'

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
                                                               'metadata': {'fees': '102'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '2',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': '102'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': '102'}
                                                           }
                                                       ]
                                                   }))
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'

        # set auth rule for revoc reg def
        req = await ledger.build_auth_rule_request(trustee_did, '113', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'OR',
                                                       'auth_constraints': [
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '0',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': '113'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '2',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': '113'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': '113'}
                                                           }
                                                       ]
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'

        # set auth rule for revoc reg entry
        req = await ledger.build_auth_rule_request(trustee_did, '114', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '*',
                                                       'sig_count': 1,
                                                       'need_to_be_owner': True,
                                                       'metadata': {'fees': '114'}
                                                   }))
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res4)
        assert res4['op'] == 'REPLY'

        # set fees
        fees = {'101': 250*100000,
                '102': 125*100000,
                '113': 100*100000,
                '114': int(0.5*100000)}
        req = await payment.build_set_txn_fees_req(wallet_handler, trustee_did, libsovtoken_payment_method,
                                                   json.dumps(fees))
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
        res5 = json.loads(await ledger.submit_request(pool_handler, req))
        print(res5)
        assert res5['op'] == 'REPLY'

        # mint tokens
        address = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps(
            {"seed": str('0000000000000000000000000Wallet0')}))
        req, _ = await payment.build_mint_req(wallet_handler, trustee_did,
                                              json.dumps([{'recipient': address, 'amount': 1000*100000}]), None)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
        res6 = json.loads(await ledger.submit_request(pool_handler, req))
        print(res6)
        assert res6['op'] == 'REPLY'

        # send schema with fees
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, adder_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req)
        source1 = \
            json.loads(await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res))[0]['source']
        schema_id, schema_json = \
            await anoncreds.issuer_create_schema(adder_did, random_string(5), '1.0', json.dumps(['name', 'age']))
        req = await ledger.build_schema_request(adder_did, schema_json)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, adder_did, req, json.dumps([source1]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': 750 * 100000}]), None)
        res7 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req_with_fees_json))
        print(res7)
        assert res7['op'] == 'REPLY'

        # send cred def with fees
        res = await get_schema(pool_handler, wallet_handler, cd_adder_did, schema_id)
        schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, cd_adder_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, cd_adder_did, req)
        source2 = \
            json.loads(await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res))[0]['source']
        cred_def_id, cred_def_json = \
            await anoncreds.issuer_create_and_store_credential_def(wallet_handler, cd_adder_did, schema_json,
                                                                   random_string(5), None,
                                                                   json.dumps({'support_revocation': True}))
        req = await ledger.build_cred_def_request(cd_adder_did, cred_def_json)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, cd_adder_did, req, json.dumps([source2]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': 625 * 100000}]), None)
        res8 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, cd_adder_did, req_with_fees_json))
        print(res8)
        assert res8['op'] == 'REPLY'

        # send revoc reg def with fees
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, cd_adder_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, cd_adder_did, req)
        source3 = \
            json.loads(await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res))[0]['source']
        tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
        tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
        revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = \
            await anoncreds.issuer_create_and_store_revoc_reg(wallet_handler, cd_adder_did, None, random_string(5),
                                                              cred_def_id, json.dumps({'max_cred_num': 1,
                                                                                       'issuance_type':
                                                                                           'ISSUANCE_BY_DEFAULT'}),
                                                              tails_writer_handle)
        req = await ledger.build_revoc_reg_def_request(cd_adder_did, revoc_reg_def_json)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, cd_adder_did, req, json.dumps([source3]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': 525 * 100000}]), None)
        res9 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, cd_adder_did, req_with_fees_json))
        print(res9)
        assert res9['op'] == 'REPLY'

        # send revoc reg entry with fees
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, cd_adder_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, cd_adder_did, req)
        source4 = \
            json.loads(await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res))[0]['source']
        req = await ledger.build_revoc_reg_entry_request\
            (cd_adder_did, revoc_reg_def_id, 'CL_ACCUM', revoc_reg_entry_json)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, cd_adder_did, req, json.dumps([source4]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': int(524.5 * 100000)}]), None)
        res10 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, cd_adder_did, req_with_fees_json))
        print(res10)
        assert res10['op'] == 'REPLY'
