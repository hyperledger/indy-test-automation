import pytest
import asyncio
from system.utils import *
from indy import payment


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestMultiSigSuite:

    @pytest.mark.asyncio
    async def test_case_sign_and_multisign(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        new_did, new_vk = await create_and_store_did(wallet_handler)
        req = ledger.build_nym_request(trustee_did, new_did, new_vk, random_string(5), None)
        # if order of sign and multisign will be changed - test fails
        req = await multi_sign_request(wallet_handler, trustee_did, req)
        req = await sign_request(wallet_handler, trustee_did, req)
        print('\n{}'.format(req))
        with pytest.raises(indy_vdr.error.VdrError):
            res = await pool_handler.submit_request(req)
            print('\n{}'.format(res))
        # assert res['op'] == 'REQNACK'

    @pytest.mark.asyncio
    async def test_case_no_any_signs(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        new_did, new_vk = await create_and_store_did(wallet_handler)
        req = ledger.build_nym_request(trustee_did, new_did, new_vk, random_string(5), None)
        print('\n{}'.format(req))
        with pytest.raises(indy_vdr.error.VdrError):
            res = await pool_handler.submit_request(req)
            print('\n{}'.format(res))
        # assert res['op'] == 'REQNACK'

    @pytest.mark.parametrize('role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR', 'NETWORK_MONITOR', None])
    @pytest.mark.asyncio
    async def test_case_anyone_can_send_nym(self, pool_handler, wallet_handler, get_default_trustee, role):
        trustee_did, _ = get_default_trustee
        new_did, new_vk = await create_and_store_did(wallet_handler)
        res1 = await send_nym(pool_handler, wallet_handler, trustee_did, new_did, new_vk, None, role)
        # assert res1['op'] == 'REPLY'
        assert res1['txnMetadata']['seqNo'] is not None
        req = ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '*',
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        # assert res2['op'] == 'REPLY'
        assert res2['txnMetadata']['seqNo'] is not None
        # await asyncio.sleep(5)
        req = ledger.build_nym_request(new_did, random_did_and_json()[0], None, None, None)
        req = await multi_sign_request(wallet_handler, new_did, req)
        res3 = await pool_handler.submit_request(req)
        # assert res3['op'] == 'REPLY'
        assert res3['txnMetadata']['seqNo'] is not None

    @pytest.mark.parametrize('role', ['STEWARD', 'TRUST_ANCHOR'])
    @pytest.mark.asyncio
    async def test_case_steward_or_trust_anchor_can_send_nym(self, pool_handler, wallet_handler, get_default_trustee,
                                                             role):
        trustee_did, _ = get_default_trustee
        new_did, new_vk = await create_and_store_did(wallet_handler)
        res1 = await send_nym(pool_handler, wallet_handler, trustee_did, new_did, new_vk, None, role)
        # assert res1['op'] == 'REPLY'
        assert res1['txnMetadata']['seqNo'] is not None
        req = ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '',
                                                   json.dumps({
                                                       'constraint_id': 'OR',
                                                       'auth_constraints': [
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '2',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {}
                                                           }
                                                       ]
                                                   }))
        res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        print(res2)
        # assert res2['op'] == 'REPLY'
        assert res2['txnMetadata']['seqNo'] is not None
        # await asyncio.sleep(5)
        req = ledger.build_nym_request(new_did, random_did_and_json()[0], None, None, None)
        req = await multi_sign_request(wallet_handler, new_did, req)
        res3 = await pool_handler.submit_request(req)
        # assert res3['op'] == 'REPLY'
        assert res3['txnMetadata']['seqNo'] is not None
        with pytest.raises(indy_vdr.error.VdrError):
            res_negative = await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
        # assert res_negative['op'] == 'REJECT'
        req = ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
        req = await multi_sign_request(wallet_handler, trustee_did, req)
        with pytest.raises(indy_vdr.error.VdrError):
            res_negative_multisign = await pool_handler.submit_request(req)
        # assert res_negative_multisign['op'] == 'REJECT'

    @pytest.mark.asyncio
    async def test_case_2_stewards_and_3_trust_anchors_can_send_nym(self, pool_handler, wallet_handler,
                                                                    get_default_trustee):
        trustee_did, _ = get_default_trustee
        s1_did, s1_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, s1_did, s1_vk, None, 'STEWARD')
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        s2_did, s2_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, s2_did, s2_vk, None, 'STEWARD')
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        t1_did, t1_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, t1_did, t1_vk, None, 'TRUST_ANCHOR')
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        t2_did, t2_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, t2_did, t2_vk, None, 'TRUST_ANCHOR')
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        t3_did, t3_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, t3_did, t3_vk, None, 'TRUST_ANCHOR')
        # assert res['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        req = ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '',
                                                   json.dumps({
                                                       'constraint_id': 'AND',
                                                       'auth_constraints': [
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '2',
                                                               'sig_count': 2,
                                                               'need_to_be_owner': False,
                                                               'metadata': {}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 3,
                                                               'need_to_be_owner': False,
                                                               'metadata': {}
                                                           }
                                                       ]
                                                   }))
        res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        # assert res2['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        # await asyncio.sleep(5)
        _req1 = ledger.build_nym_request(s1_did, random_did_and_json()[0], None, None, None)
        _req2 = await multi_sign_request(wallet_handler, s1_did, _req1)
        _req3 = await multi_sign_request(wallet_handler, s2_did, _req2)
        _req4 = await multi_sign_request(wallet_handler, t1_did, _req3)
        _req5 = await multi_sign_request(wallet_handler, t2_did, _req4)
        _req6 = await multi_sign_request(wallet_handler, t3_did, _req5)
        res3 = await pool_handler.submit_request(_req6)
        print(res3)
        # assert res3['op'] == 'REPLY'
        assert res['txnMetadata']['seqNo'] is not None
        with pytest.raises(indy_vdr.error.VdrError):
            res_negative_sign = await send_nym(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0])
        #assert res_negative_sign['op'] == 'REJECT'
        req = ledger.build_nym_request(trustee_did, random_did_and_json()[0], None, None, None)
        req = await multi_sign_request(wallet_handler, trustee_did, req)
        with pytest.raises(indy_vdr.error.VdrError):
            res_negative_multisign = await pool_handler.submit_request(req)
        #assert res_negative_multisign['op'] == 'REJECT'
