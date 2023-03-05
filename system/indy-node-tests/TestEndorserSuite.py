import pytest
import asyncio
from system.utils import *
from indy import payment
from indy_vdr.error import VdrError, VdrErrorCode

import logging

logger = logging.getLogger(__name__)


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestEndorserSuite:

    @pytest.mark.parametrize('role', [None, 'NETWORK_MONITOR', 'STEWARD', 'TRUSTEE'])
    @pytest.mark.asyncio
    async def test_case_endorser_roles(
            self, pool_handler, wallet_handler, get_default_trustee, role
    ):
        trustee_did, _ = get_default_trustee

        test_did, test_vk = await create_and_store_did(wallet_handler)
        none_did, none_vk = await create_and_store_did(wallet_handler)
        e_did, e_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, none_did, none_vk, 'Not endorser', role)
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        print(res)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, e_did, e_vk, 'Endorser', 'ENDORSER')
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        print(res)

        # negative case - build txn with endorser, append wrong role did as endorser, multisign with both
        req0 = ledger.build_nym_request(e_did, test_did, test_vk, 'Alias', None)
        req0.set_endorser(none_did)
        req0 = await multi_sign_request(wallet_handler, e_did, req0)
        req0 = await multi_sign_request(wallet_handler, none_did, req0)
        with pytest.raises(VdrError) as exp_err:
            res0 = await pool_handler.submit_request(req0)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res0['op'] == 'REJECT'

        # positive case - build txn with any role did, append endorser as endorser, multisign with both
        req1 = ledger.build_nym_request(none_did, test_did, test_vk, 'Alias', None)
        req1.set_endorser(e_did)
        req1 = await multi_sign_request(wallet_handler, none_did, req1)
        req1 = await multi_sign_request(wallet_handler, e_did, req1)
        res1 = await pool_handler.submit_request(req1)
        print(res1)
        # assert res1['op'] == 'REPLY'
        assert res1['txnMetadata']['seqNo'] is not None

    @pytest.mark.parametrize('role, result', [
        (None, 'REJECT'),
        ('NETWORK_MONITOR', 'REJECT'),
        ('ENDORSER', 'REPLY'),
        ('STEWARD', 'REPLY'),
        ('TRUSTEE', 'REPLY'),
    ])
    @pytest.mark.asyncio
    async def test_case_endorser_specification(
            self, pool_handler, wallet_handler, get_default_trustee, role, result
    ):
        trustee_did, _ = get_default_trustee
        test_did, test_vk = await create_and_store_did(wallet_handler)
        some_role_did, some_role_vk = await create_and_store_did(wallet_handler)
        e_did, e_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, some_role_did, some_role_vk, 'Not endorser', role
        )
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        res = await send_nym(pool_handler, wallet_handler, trustee_did, e_did, e_vk, 'Endorser', 'ENDORSER')
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None

        # build nym and DO NOT append endorser
        req = ledger.build_nym_request(some_role_did, test_did, test_vk, 'Alias', None)
        # but sign with two signatures
        req = await multi_sign_request(wallet_handler, some_role_did, req)
        req = await multi_sign_request(wallet_handler, e_did, req)
        if result == "REJECT":
            with pytest.raises(VdrError) as exp_err:
                res = await pool_handler.submit_request(req)
            assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == result

        # build attrib and DO NOT append endorser
        req = ledger.build_attrib_request(some_role_did, some_role_did, None, None, random_string(10))
        # but sign with two signatures
        req = await multi_sign_request(wallet_handler, some_role_did, req)
        req = await multi_sign_request(wallet_handler, e_did, req)
        if result == "REJECT":
            with pytest.raises(VdrError) as exp_err:
                res = await pool_handler.submit_request(req)
            assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == result

        # build schema and DO NOT append endorser
        schema_id, schema_json = await create_schema(
            wallet_handler, some_role_did, 'Schema 9', '9.9', json.dumps(['name', 'surname'])
        )
        req = ledger.build_schema_request(some_role_did, schema_json)
        # but sign with two signatures
        req = await multi_sign_request(wallet_handler, some_role_did, req)
        req = await multi_sign_request(wallet_handler, e_did, req)
        if result == "REJECT":
            with pytest.raises(VdrError) as exp_err:
                res = await pool_handler.submit_request(req)
            assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == result

    @pytest.mark.asyncio
    async def test_case_full_path(
            self, pool_handler, wallet_handler, get_default_trustee
    ):
        trustee_did, _ = get_default_trustee
        off_did, off_vk = await create_and_store_did(wallet_handler)
        e_did, e_vk = await create_and_store_did(wallet_handler)
        test_did, test_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, off_did, off_vk, 'No role', None)
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        res = await send_nym(pool_handler, wallet_handler, trustee_did, e_did, e_vk, 'Endorser', 'ENDORSER')
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None

        # sign nym by author only
        req = ledger.build_nym_request(off_did, test_did, test_vk, 'Alias 1', None)
        # req = await ledger.append_request_endorser(req, e_did)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, off_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # sign nym  by endorser only
        req = ledger.build_nym_request(off_did, test_did, test_vk, 'Alias 2', None)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, e_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # add new did using none role did as author and endorser did as endorser
        req0 = ledger.build_nym_request(off_did, test_did, test_vk, 'Alias 3', None)
        req0.set_endorser(e_did)
        req0 = await multi_sign_request(wallet_handler, off_did, req0)
        req0 = await multi_sign_request(wallet_handler, e_did, req0)
        res0 = await pool_handler.submit_request(req0)
        # assert res0['op'] == 'REPLY'
        assert res0['txnMetadata']['seqNo'] is not None

        schema_id, schema_json = await create_schema(
            wallet_handler, off_did, 'Schema 1', '0.1', json.dumps(['a1', 'a2'])
        )
        # sign schema by author only
        req = ledger.build_schema_request(off_did, schema_json)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, off_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # sign schema by endorser only
        req = ledger.build_schema_request(off_did, schema_json)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, e_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # add new schema using none role did as builder and endorser did as endorser
        req1 = ledger.build_schema_request(off_did, schema_json)
        req1.set_endorser(e_did)
        req1 = await multi_sign_request(wallet_handler, off_did, req1)
        req1 = await multi_sign_request(wallet_handler, e_did, req1)
        res1 = await pool_handler.submit_request(req1)
        print(res1)
        #assert res1['op'] == 'REPLY'
        assert res1['txnMetadata']['seqNo'] is not None

        await asyncio.sleep(1)
        res = await get_schema(pool_handler, wallet_handler, trustee_did, schema_id)
        schema_id, schema_json = parse_get_schema_response(res)
        cred_def_id, cred_def_json = await create_and_store_cred_def(
            wallet_handler, off_did, schema_json, 'cred def tag', None, support_revocation=True
        )
        # sign cred def by author only
        req = ledger.build_cred_def_request(off_did, cred_def_json)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, off_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # sign cred def by endorser only
        req = ledger.build_cred_def_request(off_did, cred_def_json)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, e_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # add new cred def using none role did as builder and endorser did as endorser
        req2 = ledger.build_cred_def_request(off_did, cred_def_json)
        req2.set_endorser(e_did)
        req2 = await multi_sign_request(wallet_handler, off_did, req2)
        req2 = await multi_sign_request(wallet_handler, e_did, req2)
        res2 = await pool_handler.submit_request(req2)
        print(res2)
        # assert res2['op'] == 'REPLY'
        assert res2['txnMetadata']['seqNo'] is not None

        # tails_writer_config = json.dumps({'base_dir': 'tails', 'uri_pattern': ''})
        # tails_writer_handle = await blob_storage.open_writer('default', tails_writer_config)
        revoc_reg_id, revoc_reg_def_json, revoc_reg_entry_json = await create_and_store_revoc_reg(
            wallet_handler, off_did, 'CL_ACCUM', 'revoc reg tag', cred_def_id,
                max_cred_num=100, issuance_type='ISSUANCE_BY_DEFAULT'
        )
        # sign revoc reg def by author only
        req = ledger.build_revoc_reg_def_request(off_did, revoc_reg_def_json)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, off_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # sign revoc reg def by endorser only
        req = ledger.build_revoc_reg_def_request(off_did, revoc_reg_def_json)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, e_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # add new revoc reg def using none role did as builder and endorser did as endorser
        req3 = ledger.build_revoc_reg_def_request(off_did, revoc_reg_def_json)
        req3.set_endorser(e_did)
        req3 = await multi_sign_request(wallet_handler, off_did, req3)
        req3 = await multi_sign_request(wallet_handler, e_did, req3)
        res3 = await pool_handler.submit_request(req3)
        print(res3)
        # assert res3['op'] == 'REPLY'
        assert res3['txnMetadata']['seqNo'] is not None

        # sign revoc reg entry by author only
        req = ledger.build_revoc_reg_entry_request(off_did, revoc_reg_id, 'CL_ACCUM', revoc_reg_entry_json)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, off_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # sign revoc reg entry by endorser only
        req = ledger.build_revoc_reg_entry_request(off_did, revoc_reg_id, 'CL_ACCUM', revoc_reg_entry_json)
        req.set_endorser(e_did)
        req = await multi_sign_request(wallet_handler, e_did, req)
        with pytest.raises(VdrError) as exp_err:
            res = await pool_handler.submit_request(req)
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED
        # assert res['op'] == 'REQNACK'
        # add new revoc reg entry using none role did as builder and endorser did as endorser
        req4 = ledger.build_revoc_reg_entry_request(off_did, revoc_reg_id, 'CL_ACCUM', revoc_reg_entry_json)
        req4.set_endorser(e_did)
        req4 = await multi_sign_request(wallet_handler, off_did, req4)
        req4 = await multi_sign_request(wallet_handler, e_did, req4)
        res4 = await pool_handler.submit_request(req4)
        print(res4)
        # assert res4['op'] == 'REPLY'
        assert res4['txnMetadata']['seqNo'] is not None