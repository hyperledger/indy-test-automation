import pytest
from system.utils import *
from async_generator import async_generator, yield_


method_name = 'fqdid'


# setup once for all cases
@pytest.fixture(scope='module', autouse=True)
@async_generator
async def docker_setup_and_teardown(docker_setup_and_teardown_module):
    await yield_()


class TestFQDIDsSuite:

    @pytest.mark.asyncio
    async def test_case_basic_functionality(
            self, pool_handler, wallet_handler
    ):
        # create FQDID and unqualify it
        did_1, vk_1 = await did.create_and_store_my_did(wallet_handler, json.dumps({'method_name': method_name}))
        assert did_1.__contains__('did:{}:'.format(method_name))
        did_1 = await anoncreds.to_unqualified(did_1)
        assert not did_1.__contains__('did:{}:'.format(method_name))

        # create common DID and qualify it
        did_2, vk_2 = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
        assert not did_2.__contains__('did:{}:'.format(method_name))
        did_2 = await did.qualify_did(wallet_handler, did_2, method_name)
        assert did_2.__contains__('did:{}:'.format(method_name))

    @pytest.mark.parametrize('ver', ['1.0', '2.0'])
    @pytest.mark.parametrize('is_issuer_fq', [True, False])
    @pytest.mark.parametrize('is_prover_fq', [True, False])
    @pytest.mark.asyncio
    async def test_case_full_path_positive(
            self, pool_handler, wallet_handler, get_default_trustee, is_issuer_fq, is_prover_fq, ver
    ):
        trustee_did, trustee_vk = get_default_trustee
        issuer_param = {'method_name': method_name} if is_issuer_fq else {}
        prover_param = {'method_name': method_name} if is_prover_fq else {}

        issuer_did, issuer_vk = await did.create_and_store_my_did(wallet_handler, json.dumps(issuer_param))
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, issuer_did, issuer_vk, 'ISSUER', 'ENDORSER'
        )
        assert res['op'] == 'REPLY'

        prover_did, prover_vk = await did.create_and_store_my_did(wallet_handler, json.dumps(prover_param))
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, prover_did, prover_vk, 'PROVER', 'ENDORSER'
        )
        assert res['op'] == 'REPLY'

        schema_id, res1 = await send_schema(
            pool_handler, wallet_handler, issuer_did, 'Passport Schema', '1.0', json.dumps(['Name', 'Age'])
        )
        assert res1['op'] == 'REPLY'

        res = await get_schema(pool_handler, wallet_handler, issuer_did, schema_id)
        schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
        cred_def_id, cred_def_json, res2 = await send_cred_def(
            pool_handler, wallet_handler, issuer_did, schema_json, 'Cred Def Tag', 'CL', json.dumps(
                {'support_revocation': True}
            )
        )
        assert res2['op'] == 'REPLY'

        cred_offer_json = await anoncreds.issuer_create_credential_offer(wallet_handler, cred_def_id)

        ms_id = await anoncreds.prover_create_master_secret(wallet_handler, 'Master secret 1')
        cred_req_json, cred_req_metadata_json = await anoncreds.prover_create_credential_req(
            wallet_handler, prover_did, cred_offer_json, cred_def_json, ms_id
        )
        cred_json, cred_revoc_id, revoc_reg_delta_json = await anoncreds.issuer_create_credential(
            wallet_handler, cred_offer_json, cred_req_json, json.dumps(
                {
                    "Name":
                        {
                            "raw": "Pyotr",
                            "encoded": "111"
                        },
                    "Age":
                        {
                            "raw": "99",
                            "encoded": "222"
                        }
                }
            ), None, None
        )
        cred_id = await anoncreds.prover_store_credential(
            wallet_handler, None, cred_req_metadata_json, cred_json, cred_def_json, None
        )

        # proof request
        proof_request = json.dumps(
            {
                "nonce": "123432421212",
                "name": "proof_req_1",
                "version": "0.1",
                "ver": ver,
                "requested_attributes":
                    {
                        "attr1_referent":
                            {
                                "name": "Name"
                            }
                    },
                "requested_predicates":
                    {
                        "predicate1_referent":
                            {
                                "name": "Age", "p_type": ">=", "p_value": 18
                            }
                    }
            }
        )
        credentials_json = json.loads(
            await anoncreds.prover_get_credentials_for_proof_req(wallet_handler, proof_request)
        )
        search_handle = await anoncreds.prover_search_credentials_for_proof_req(wallet_handler, proof_request, None)

        creds_for_attr1 = await anoncreds.prover_fetch_credentials_for_proof_req(
            search_handle, 'attr1_referent', 10
        )
        cred_for_attr1 = json.loads(creds_for_attr1)[0]['cred_info']

        creds_for_predicate1 = await anoncreds.prover_fetch_credentials_for_proof_req(
            search_handle, 'predicate1_referent', 10
        )
        cred_for_predicate1 = json.loads(creds_for_predicate1)[0]['cred_info']

        await anoncreds.prover_close_credentials_search_for_proof_req(search_handle)

        # primary proof
        requested_credentials_json = json.dumps(
            {
                "self_attested_attributes": {},
                "requested_attributes":
                    {
                        "attr1_referent":
                            {
                                "cred_id": cred_for_attr1['referent'],
                                "revealed": True
                            }
                    },
                "requested_predicates":
                    {
                        "predicate1_referent":
                            {
                                "cred_id": cred_for_predicate1['referent']
                            }
                    }
            }
        )

        schemas_json = json.dumps(
            {cred_for_attr1['schema_id']: json.loads(schema_json)}
        )
        cred_defs_json = json.dumps(
            {cred_for_attr1['cred_def_id']: json.loads(cred_def_json)}
        )

        proof = await anoncreds.prover_create_proof(
            wallet_handler, proof_request, requested_credentials_json, ms_id, schemas_json, cred_defs_json, '{}'
        )
        proof_as_dict = json.loads(proof)

        if is_issuer_fq and ver == '2.0':  # the only condition for fq ids
            assert proof_as_dict['identifiers'][0]['schema_id'].__contains__(
                'schema:{0}:did:{0}'.format(method_name)
            )
            assert proof_as_dict['identifiers'][0]['cred_def_id'].__contains__(
                'creddef:{0}:did:{0}'.format(method_name)
            )
        else:  # all other cases have uq ids
            assert not proof_as_dict['identifiers'][0]['schema_id'].__contains__(
                'schema:{0}:did:{0}'.format(method_name)
            )
            assert not proof_as_dict['identifiers'][0]['cred_def_id'].__contains__(
                'creddef:{0}:did:{0}'.format(method_name)
            )

        # generate this entities again according to new logic
        schemas_json = json.dumps(
            {proof_as_dict['identifiers'][0]['schema_id']: json.loads(schema_json)}
        )
        cred_defs_json = json.dumps(
            {proof_as_dict['identifiers'][0]['cred_def_id']: json.loads(cred_def_json)}
        )

        assert 'Pyotr' == proof_as_dict['requested_proof']['revealed_attrs']['attr1_referent']['raw']
        assert await anoncreds.verifier_verify_proof(proof_request, proof, schemas_json, cred_defs_json, '{}', '{}')

    @pytest.mark.asyncio
    async def test_case_special(
            self, pool_handler, wallet_handler, get_default_trustee
    ):
        trustee_did, trustee_vk = get_default_trustee

        # FQ issuer
        issuer_did, issuer_vk = await did.create_and_store_my_did(
            wallet_handler, json.dumps({'method_name': method_name})
        )
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, issuer_did, issuer_vk, 'ISSUER', 'ENDORSER'
        )
        assert res['op'] == 'REPLY'

        # common prover
        prover_did, prover_vk = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, prover_did, prover_vk, 'PROVER', 'ENDORSER'
        )
        assert res['op'] == 'REPLY'

        schema_id, res1 = await send_schema(
            pool_handler, wallet_handler, issuer_did, 'Passport Schema', '1.0', json.dumps(['Name', 'Age'])
        )
        assert res1['op'] == 'REPLY'
        # schema is fq
        assert schema_id.__contains__('schema:{0}:did:{0}'.format(method_name))

        # unqualify schema_id from anoncreds
        _schema_id = await anoncreds.to_unqualified(schema_id)
        # schema is uq
        assert not _schema_id.__contains__('schema:{0}:did:{0}'.format(method_name))

        res = await get_schema(pool_handler, wallet_handler, issuer_did, schema_id)
        schema_id, schema_json = await ledger.parse_get_schema_response(json.dumps(res))
        # schema from ledger is always uq
        assert not schema_id.__contains__('schema:{0}:did:{0}'.format(method_name))

        # unqualify schema_id from ledger
        __schema_id = await anoncreds.to_unqualified(schema_id)
        # schema from ledger remains the same (uq)
        assert not __schema_id.__contains__('schema:{0}:did:{0}'.format(method_name))

        cred_def_id, cred_def_json, res2 = await send_cred_def(
            pool_handler, wallet_handler, issuer_did, schema_json, 'Cred Def Tag', 'CL', json.dumps(
                {'support_revocation': True}
            )
        )
        assert res2['op'] == 'REPLY'
        # cred def is fq
        assert cred_def_id.__contains__('creddef:{0}:did:{0}'.format(method_name))

        # unqualify cred_def_id from anoncreds
        _cred_def_id = await anoncreds.to_unqualified(cred_def_id)
        # cred def is uq
        assert not _cred_def_id.__contains__('creddef:{0}:did:{0}'.format(method_name))

        revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json, res3 = await send_revoc_reg_def(
            pool_handler, wallet_handler, issuer_did, 'CL_ACCUM', 'Revoc Reg Def Tag', cred_def_id, json.dumps(
                {'max_cred_num': 10, 'issuance_type': 'ISSUANCE_BY_DEFAULT'}
            )
        )
        assert res3['op'] == 'REPLY'
        # revoc reg def is fq
        assert revoc_reg_def_id.__contains__('revreg:{0}:did:{0}'.format(method_name))

        # unqualify revoc_reg_def_id from anoncreds
        _revoc_reg_def_id = await anoncreds.to_unqualified(revoc_reg_def_id)
        # revoc reg def is uq
        assert not _revoc_reg_def_id.__contains__('revreg:{0}:did:{0}'.format(method_name))

        cred_offer_json = await anoncreds.issuer_create_credential_offer(wallet_handler, cred_def_id)
        cred_offer_as_dict = json.loads(cred_offer_json)
        assert cred_offer_as_dict['schema_id'].__contains__('schema:{0}:did:{0}'.format(method_name))
        assert cred_offer_as_dict['cred_def_id'].__contains__('creddef:{0}:did:{0}'.format(method_name))

        # unqualify cred_offer_json from anoncreds
        _cred_offer_json = await anoncreds.to_unqualified(cred_offer_json)
        _cred_offer_as_dict = json.loads(_cred_offer_json)
        assert not _cred_offer_as_dict['schema_id'].__contains__('schema:{0}:did:{0}'.format(method_name))
        assert not _cred_offer_as_dict['cred_def_id'].__contains__('creddef:{0}:did:{0}'.format(method_name))

        ms_id = await anoncreds.prover_create_master_secret(wallet_handler, 'Master secret 2')
        # use uq cred_offer
        cred_req_json, cred_req_metadata_json = await anoncreds.prover_create_credential_req(
            wallet_handler, prover_did, _cred_offer_json, cred_def_json, ms_id
        )
        cred_req_as_dict = json.loads(cred_req_json)
        assert not cred_req_as_dict['cred_def_id'].__contains__('creddef:{0}:did:{0}'.format(method_name))
