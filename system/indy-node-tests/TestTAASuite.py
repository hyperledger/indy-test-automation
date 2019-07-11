import pytest
from system.utils import *
from indy import payment
# from hypothesis import strategies, settings, given
SEC_PER_DAY = 24 * 60 * 60


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestTAASuite:

    @pytest.mark.parametrize('aml, version_set, context, timestamp, version_get', [
        ({random_string(10): random_string(10)}, '0', random_string(25), None, '0'),
        ({random_string(100): random_string(100)}, random_string(5), None,
         int(time.time()) // SEC_PER_DAY * SEC_PER_DAY, None)
    ])
    @pytest.mark.asyncio
    async def test_case_send_and_get_aml(
            self, pool_handler, wallet_handler, get_default_trustee, aml, version_set, context, timestamp, version_get
    ):
        trustee_did, _ = get_default_trustee
        req = await ledger.build_acceptance_mechanisms_request(trustee_did, json.dumps(aml), version_set, context)
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res1)
        assert res1['op'] == 'REPLY'
        # aml with the same version should be rejected
        req = await ledger.build_acceptance_mechanisms_request(trustee_did, json.dumps(aml), version_set, context)
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REJECT'
        req = await ledger.build_get_acceptance_mechanisms_request(None, timestamp, version_get)
        res3 = json.loads(await ledger.submit_request(pool_handler, req))
        print(res3)
        assert res3['op'] == 'REPLY'

    @pytest.mark.parametrize('taa_text, taa_ver', [
        (random_string(1), random_string(100)),
        (random_string(100), random_string(1))
    ])
    @pytest.mark.asyncio
    async def test_case_send_and_get_taa(self, pool_handler, wallet_handler, get_default_trustee, taa_text, taa_ver):
        trustee_did, _ = get_default_trustee
        # no aml in ledger - should be rejected
        req = await ledger.build_txn_author_agreement_request(trustee_did, taa_text, taa_ver)
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res1)
        assert res1['op'] == 'REJECT'
        aml_key = 'aml_key'
        req = await ledger.build_acceptance_mechanisms_request(
            trustee_did, json.dumps({aml_key: random_string(5)}), random_string(10), None
        )
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        req = await ledger.build_txn_author_agreement_request(trustee_did, taa_text, taa_ver)
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        # no taa in nym request
        res4 = await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
        print(res4)
        assert res4['op'] == 'REJECT'
        # no taa in schema request
        _, res5 = await send_schema(
            pool_handler, wallet_handler, trustee_did, random_string(5), '1.0', json.dumps([random_string(10)])
        )
        print(res5)
        assert res5['op'] == 'REJECT'
        # add taa to nym
        req6 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
        req6 = await ledger.append_txn_author_agreement_acceptance_to_request(
            req6, taa_text, taa_ver, None, aml_key, int(time.time()) // SEC_PER_DAY * SEC_PER_DAY
        )
        res6 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req6))
        print(res6)
        assert res6['op'] == 'REPLY'
        # add taa to schema
        schema_id, schema_json = await anoncreds.issuer_create_schema(
            trustee_did, random_string(5), '1.0', json.dumps([random_string(10)])
        )
        req = await ledger.build_schema_request(trustee_did, schema_json)
        req = await ledger.append_txn_author_agreement_acceptance_to_request(
            req, taa_text, taa_ver, None, aml_key, int(time.time()) // SEC_PER_DAY * SEC_PER_DAY
        )
        res7 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res7)
        assert res7['op'] == 'REPLY'
        # special positive case
        req8 = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
        req8 = await ledger.append_txn_author_agreement_acceptance_to_request(
            req8, taa_text, taa_ver, None, aml_key, int(time.time()) // SEC_PER_DAY * SEC_PER_DAY
        )
        await asyncio.sleep(181)
        res8 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req8))
        print(res8)
        assert res8['op'] == 'REPLY'

    @pytest.mark.asyncio
    async def test_aml_taa_negative_cases(self, pool_handler, wallet_handler, get_default_trustee):
        aml = {}
        aml_key = aml_ver = taa_ver = random_string(5)
        aml_val = taa_text = random_string(25)
        trustee_did, _ = get_default_trustee
        req = {
            'protocolVersion': 2,
            'reqId': 1,
            'identifier': trustee_did,
            'operation': {
                'type': '5',
                'aml': aml,
                'version': '1'
                }
            }
        print(json.dumps(req))
        res1 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, json.dumps(req))
        )
        print(res1)
        assert res1['op'] == 'REQNACK'
        req = await ledger.build_txn_author_agreement_request(trustee_did, 'text', '1')
        res2 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        )
        print(res2)
        assert res2['op'] == 'REJECT'
        req = await ledger.build_acceptance_mechanisms_request(
            trustee_did, json.dumps({aml_key: aml_val}), aml_ver, None
        )
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        req = await ledger.build_txn_author_agreement_request(trustee_did, taa_text, taa_ver)
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res4)
        assert res4['op'] == 'REPLY'
        # send txn with taa with precise timestamp
        req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
        req = await ledger.append_txn_author_agreement_acceptance_to_request(
            req, taa_text, taa_ver, None, aml_key, int(time.time())
        )
        res6 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res6)
        assert res6['op'] == 'REJECT'
        # send txn with taa with timestamp from yesterday
        req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
        req = await ledger.append_txn_author_agreement_acceptance_to_request(
            req, taa_text, taa_ver, None, aml_key, int(time.time()) // SEC_PER_DAY * SEC_PER_DAY - SEC_PER_DAY
        )
        res7 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res7)
        assert res7['op'] == 'REJECT'
        # send txn with taa with timestamp from tomorrow
        req = await ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
        req = await ledger.append_txn_author_agreement_acceptance_to_request(
            req, taa_text, taa_ver, None, aml_key, int(time.time()) // SEC_PER_DAY * SEC_PER_DAY + SEC_PER_DAY
        )
        res8 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res8)
        assert res8['op'] == 'REJECT'

    @pytest.mark.asyncio
    async def test_case_taa_with_xfer(
            self, payment_init, pool_handler, wallet_handler, get_default_trustee, initial_token_minting
    ):
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        address1 = initial_token_minting
        address2 = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, json.dumps({}))
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address1)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        source1 = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res)
        )[0]['source']
        aml_key = 'aml_key'
        taa_text = 'some TAA text'
        taa_ver = 'some TAA version'
        # try to send xfer with taa without aml and taa in ledger - should be failed
        extra = await payment.prepare_payment_extra_with_acceptance_data(
            None, taa_text, taa_ver, None, aml_key, int(time.time()) // SEC_PER_DAY * SEC_PER_DAY
        )
        req, _ = await payment.build_payment_req(
            wallet_handler, trustee_did,  json.dumps([source1]),
            json.dumps([{"recipient": address2, "amount": 100*100000}, {"recipient": address1, "amount": 900*100000}]),
            extra)
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res1)
        assert res1['op'] == 'REJECT'
        req = await ledger.build_acceptance_mechanisms_request(
            trustee_did, json.dumps({aml_key: random_string(5)}), random_string(10), None
        )
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res2)
        assert res2['op'] == 'REPLY'
        req = await ledger.build_txn_author_agreement_request(trustee_did, taa_text, taa_ver)
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        extra = await payment.prepare_payment_extra_with_acceptance_data(
            None, taa_text, taa_ver, None, aml_key, int(time.time()) // SEC_PER_DAY * SEC_PER_DAY
        )
        req, _ = await payment.build_payment_req(
            wallet_handler, trustee_did, json.dumps([source1]),
            json.dumps([{"recipient": address2, "amount": 100*100000}, {"recipient": address1, "amount": 900*100000}]),
            extra)
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res4)
        assert res4['op'] == 'REPLY'
        # try to send xfer without taa to ledger with aml and taa - should be failed
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address1)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        source2 = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res)
        )[0]['source']
        req, _ = await payment.build_payment_req(
            wallet_handler, trustee_did, json.dumps([source2]),
            json.dumps([{"recipient": address2, "amount": 200*100000}, {"recipient": address1, "amount": 700*100000}]),
            None)
        res5 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res5)
        assert res5['op'] == 'REJECT'
