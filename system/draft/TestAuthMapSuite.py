import pytest
from system.utils import *


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestAuthMapSuite:

    @pytest.mark.asyncio
    async def test_case_attrib(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        # add target nym
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, target_did, target_vk)
        assert res['op'] == 'REPLY'
        # add steward to add attrib
        s1_did, s1_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, s1_did, s1_vk, None, 'STEWARD')
        assert res['op'] == 'REPLY'
        # add trustee to edit attrib
        t1_did, t1_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, t1_did, t1_vk, None, 'TRUSTEE')
        assert res['op'] == 'REPLY'
        # set rule for adding
        req = await ledger.build_auth_rule_request(trustee_did, '100', 'ADD', '*', None, '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '2',
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
                                                       'role': '0',
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'
        # add attrib for target did by non-owner Steward
        res4 = await send_attrib(pool_handler, wallet_handler, s1_did, target_did,
                                 None, json.dumps({'key': 'value1'}), None)
        print(res4)
        assert res4['op'] == 'REPLY'
        # edit attrib for target did by non-owner Trustee
        res5 = await send_attrib(pool_handler, wallet_handler, t1_did, target_did,
                                 None, json.dumps({'key': 'value2'}), None)
        print(res5)
        assert res5['op'] == 'REPLY'
