import pytest
import asyncio
from system_payments_only.utils import *
from indy import payment

import logging
logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestEndorserSuite:


    @pytest.mark.asyncio
    async def test_case_endorser_special_case(
            self, payment_init, pool_handler, wallet_handler, get_default_trustee,
            initial_token_minting, initial_fees_setting
    ):
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        address = initial_token_minting
        author_did, author_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        e_did, e_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, author_did, author_vk, 'No role', None)
        assert res['op'] == 'REPLY'
        res = await send_nym(pool_handler, wallet_handler, trustee_did, e_did, e_vk, 'Endorser', 'ENDORSER')
        assert res['op'] == 'REPLY'

        # set fees
        print(initial_fees_setting)

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
                                                               'metadata': {'fees': 'add_schema_250'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '2',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_schema_250'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_schema_250'}
                                                           }
                                                       ]
                                                   }))
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res1)
        assert res1['op'] == 'REPLY'

        # add endorser first
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, author_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, author_did, req)
        source1 = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res)
        )[0]['source']
        schema_id, schema_json = await anoncreds.issuer_create_schema(
            author_did, random_string(5), '1.0', json.dumps(['name', 'age'])
        )
        req = await ledger.build_schema_request(author_did, schema_json)
        req = await ledger.append_request_endorser(req, e_did)
        req_with_fees_json, _ = await payment.add_request_fees(
            wallet_handler, author_did, req, json.dumps([source1]), json.dumps(
                [{'recipient': address, 'amount': 750 * 100000}]
            ), None
        )
        req_with_fees_json = await ledger.multi_sign_request(wallet_handler, author_did, req_with_fees_json)
        req_with_fees_json = await ledger.multi_sign_request(wallet_handler, e_did, req_with_fees_json)
        print(req_with_fees_json)
        res2 = json.loads(await ledger.submit_request(pool_handler, req_with_fees_json))
        print(res2)
        assert res2['op'] == 'REPLY'

        # add fees first
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, author_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, author_did, req)
        source2 = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res)
        )[0]['source']
        schema_id, schema_json = await anoncreds.issuer_create_schema(
            author_did, random_string(5), '0.1', json.dumps(['age', 'name'])
        )
        req = await ledger.build_schema_request(author_did, schema_json)
        req_with_fees_json, _ = await payment.add_request_fees(
            wallet_handler, author_did, req, json.dumps([source2]), json.dumps(
                [{'recipient': address, 'amount': 500 * 100000}]
            ), None
        )
        req_with_fees_json = await ledger.append_request_endorser(req_with_fees_json, e_did)
        req_with_fees_json = await ledger.multi_sign_request(wallet_handler, author_did, req_with_fees_json)
        req_with_fees_json = await ledger.multi_sign_request(wallet_handler, e_did, req_with_fees_json)
        print(req_with_fees_json)
        res3 = json.loads(await ledger.submit_request(pool_handler, req_with_fees_json))
        print(res3)
        assert res3['op'] == 'REJECT'

    @pytest.mark.asyncio
    async def test_case_endorser_production_fees(
            self, payment_init, pool_handler, wallet_handler, get_default_trustee,
            initial_token_minting, initial_fees_setting
    ):
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        address = initial_token_minting
        author_did, author_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        e_did, e_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, author_did, author_vk, 'No role', None)
        assert res['op'] == 'REPLY'
        res = await send_nym(pool_handler, wallet_handler, trustee_did, e_did, e_vk, 'Endorser', 'ENDORSER')
        assert res['op'] == 'REPLY'

        # set fees
        print(initial_fees_setting)

        # set auth rule for schema
        req = await ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'OR',
                                                       'auth_constraints': [
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '*',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_schema_250'}
                                                           }
                                                       ]
                                                   }))
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res1)
        assert res1['op'] == 'REPLY'

        schema_id, schema_json = await anoncreds.issuer_create_schema(
            author_did, random_string(5), '1.0', json.dumps([random_string(10), random_string(15), random_string(20)])
        )

        req, _ = await payment.build_get_payment_sources_request(wallet_handler, author_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, author_did, req)
        source1 = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res)
        )[0]['source']

        # try to add schema without fees and endorser - should fail
        req = await ledger.build_schema_request(author_did, schema_json)
        res2 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, author_did, req)
        )
        print(res2)
        assert res2['op'] == 'REJECT'

        # add schema with endorser only
        req = await ledger.build_schema_request(e_did, schema_json)
        res3 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, e_did, req)
        )
        print(res3)
        assert res3['op'] == 'REPLY'

        # add schema with author with wrong role endorser and fees - should fail
        req = await ledger.build_schema_request(author_did, schema_json)
        req = await ledger.append_request_endorser(req, trustee_did)
        req, _ = await payment.add_request_fees(
            wallet_handler, author_did, req, json.dumps([source1]), json.dumps(
                [{'recipient': address, 'amount': 750 * 100000}]
            ), None
        )
        req = await ledger.multi_sign_request(wallet_handler, author_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        res4 = json.loads(await ledger.submit_request(pool_handler, req))
        print(res4)
        assert res4['op'] == 'REJECT'

        # add schema with author with fees
        req = await ledger.build_schema_request(author_did, schema_json)
        req, _ = await payment.add_request_fees(
            wallet_handler, author_did, req, json.dumps([source1]), json.dumps(
                [{'recipient': address, 'amount': 750 * 100000}]
            ), None
        )
        res5 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, author_did, req)
        )
        print(res5)
        assert res5['op'] == 'REPLY'

        # add schema with author with endorser
        schema_id, schema_json = await anoncreds.issuer_create_schema(
            author_did, random_string(5), '2.0', json.dumps([random_string(10), random_string(15), random_string(20)])
        )
        req = await ledger.build_schema_request(author_did, schema_json)
        req = await ledger.append_request_endorser(req, e_did)
        req = await ledger.multi_sign_request(wallet_handler, author_did, req)
        req = await ledger.multi_sign_request(wallet_handler, e_did, req)
        res6 = json.loads(await ledger.submit_request(pool_handler, req))
        print(res6)
        assert res6['op'] == 'REPLY'
