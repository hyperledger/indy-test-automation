import pytest
from system.utils import *
from indy import payment


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestFeesSuite:

    @pytest.mark.asyncio
    async def test_case_trustee(self, pool_handler, wallet_handler, get_default_trustee, initial_fees_setting):
        trustee_did, _ = get_default_trustee
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')

        print(initial_fees_setting)

        # set auth rule for trustee adding
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '0',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trustee_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for trustee -> steward
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '0', '2',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trustee_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for trustee -> trust anchor
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '0', '101',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trustee_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for trustee -> network monitor
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '0', '201',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trustee_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for trustee -> identity owner
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '0', None,
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trustee_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # try to add trustee with one trustee (default rule) - should be rejected
        new_t_did, new_t_vk = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
        res6 = await send_nym(pool_handler, wallet_handler, trustee_did, new_t_did, new_t_vk, 'new trustee', 'TRUSTEE')
        print(res6)
        assert res6['op'] == 'REJECT'
        # add new trustee according to new rule
        req = await ledger.build_nym_request(trustee_did, new_t_did, new_t_vk, 'new trustee', 'TRUSTEE')
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
        res66 = json.loads(await ledger.submit_request(pool_handler, req))
        print(res66)
        assert res66['op'] == 'REPLY'

        # TODO add edit actions

    @pytest.mark.asyncio
    async def test_case_steward(self, pool_handler, wallet_handler, get_default_trustee, initial_fees_setting):
        trustee_did, _ = get_default_trustee
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')

        print(initial_fees_setting)

        # set auth rule for steward adding
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '2',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'steward_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for steward -> trustee
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '2', '0',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'steward_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for steward -> trust anchor
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '2', '101',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'steward_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for steward -> network monitor
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '2', '201',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'steward_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for steward -> identity owner
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '2', None,
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'steward_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # try to add steward with one trustee (default rule) - should be rejected
        new_s_did, new_s_vk = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
        res7 = await send_nym(pool_handler, wallet_handler, trustee_did, new_s_did, new_s_vk, 'new steward', 'STEWARD')
        print(res7)
        assert res7['op'] == 'REJECT'
        # add new trustee according to new rule
        req = await ledger.build_nym_request(trustee_did, new_s_did, new_s_vk, 'new steward', 'STEWARD')
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
        res77 = json.loads(await ledger.submit_request(pool_handler, req))
        print(res77)
        assert res77['op'] == 'REPLY'

        # TODO add edit actions

    @pytest.mark.asyncio
    async def test_case_trust_anchor(self, pool_handler, wallet_handler, get_default_trustee, initial_fees_setting):
        trustee_did, _ = get_default_trustee
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Steward1')}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, 'STEWARD')

        print(initial_fees_setting)

        # set auth rule for trust anchor adding
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '101',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trust_anchor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for trust anchor -> trustee
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '101', '0',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trust_anchor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for trust anchor -> steward
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '101', '2',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trust_anchor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for trust anchor -> network monitor
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '101', '201',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trust_anchor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for trust anchor -> identity owner
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '101', None,
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'trust_anchor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # try to add trust anchor with one steward (default rule) - should be rejected
        new_ta_did, new_ta_vk = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
        res8 = await send_nym\
            (pool_handler, wallet_handler, steward_did, new_ta_did, new_ta_vk, 'new TA', 'TRUST_ANCHOR')
        print(res8)
        assert res8['op'] == 'REJECT'
        # add new trust anchor according to new rule
        res88 = await send_nym\
            (pool_handler, wallet_handler, trustee_did, new_ta_did, new_ta_vk, 'new TA', 'TRUST_ANCHOR')
        print(res88)
        assert res88['op'] == 'REPLY'

        # TODO add edit actions

    @pytest.mark.asyncio
    async def test_case_network_monitor(self, pool_handler, wallet_handler, get_default_trustee, initial_fees_setting):
        trustee_did, _ = get_default_trustee
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        ta_did, ta_vk = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Steward1')}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, ta_did, ta_vk, None, 'TRUST_ANCHOR')

        print(initial_fees_setting)

        # set auth rule for network monitor adding
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', '201',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'network_monitor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for network monitor -> trustee
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '201', '0',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'network_monitor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for network monitor -> steward
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '201', '2',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'network_monitor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for network monitor -> trust anchor
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '201', '101',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'network_monitor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for network monitor -> identity owner
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', '201', None,
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'network_monitor_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # try to add network monitor with one trust anchor (default rule) - should be rejected
        new_nm_did, new_nm_vk = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
        res9 = await send_nym\
            (pool_handler, wallet_handler, ta_did, new_nm_did, new_nm_vk, 'new NM', 'NETWORK_MONITOR')
        print(res9)
        assert res9['op'] == 'REJECT'
        # add new trust anchor according to new rule
        res99 = await send_nym\
            (pool_handler, wallet_handler, trustee_did, new_nm_did, new_nm_vk, 'new NM', 'NETWORK_MONITOR')
        print(res99)
        assert res99['op'] == 'REPLY'

        # TODO add edit actions

    @pytest.mark.asyncio
    async def test_case_identity_owner(self, pool_handler, wallet_handler, get_default_trustee, initial_fees_setting,
                                       initial_token_minting):
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        ta_did, ta_vk = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Steward1')}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, ta_did, ta_vk, None, 'TRUST_ANCHOR')

        print(initial_fees_setting)
        address = initial_token_minting

        # set auth rule for identity owner adding
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', None,
                                                   json.dumps({
                                                       'constraint_id': 'OR',
                                                       'auth_constraints': [
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '0',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_identity_owner_50'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '2',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_identity_owner_50'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_identity_owner_50'}
                                                           }
                                                       ]
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for identity owner -> trustee
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', None, '0',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'edit_identity_owner_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for identity owner -> steward
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', None, '2',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'edit_identity_owner_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for identity owner -> trust anchor
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', None, '101',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'edit_identity_owner_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # set auth rule for identity owner -> network monitor
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'EDIT', 'role', None, '201',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '0',
                                                       'sig_count': 3,
                                                       'need_to_be_owner': False,
                                                       'metadata': {'fees': 'edit_identity_owner_0'}
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res)
        assert res['op'] == 'REPLY'

        # try to add identity owner with one trust anchor without fees (default rule) - should be rejected
        new_io_did, new_io_vk = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
        res = await send_nym\
            (pool_handler, wallet_handler, ta_did, new_io_did, new_io_vk, 'new IO', None)
        print(res)
        assert res['op'] == 'REJECT'
        # add new identity owner according to new rule
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, ta_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, ta_did, req)
        source1 = \
            json.loads(await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res))[0]['source']
        req = await ledger.build_nym_request(ta_did, new_io_did, new_io_vk, 'new IO', None)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, ta_did, req, json.dumps([source1]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': 950 * 100000}]), None)
        res10 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, ta_did, req_with_fees_json))
        print(res10)
        assert res10['op'] == 'REPLY'

        # TODO add edit actions

    @pytest.mark.parametrize('schema_adder_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
    @pytest.mark.parametrize('cred_def_adder_role', ['TRUSTEE', 'STEWARD', 'TRUST_ANCHOR'])
    @pytest.mark.asyncio
    async def test_case_schema_cred_def_rrd_rre(self, pool_handler, wallet_handler, get_default_trustee,
                                                initial_token_minting, schema_adder_role, cred_def_adder_role):
        await payment_initializer('libsovtoken.so', 'sovtoken_init')
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        address = initial_token_minting
        trustee_did2, trustee_vk2 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee2')}))
        trustee_did3, trustee_vk3 = await did.create_and_store_my_did(wallet_handler, json.dumps(
            {"seed": str('000000000000000000000000Trustee3')}))
        io_did, io_vk = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
        await send_nym(pool_handler, wallet_handler, trustee_did, io_did, io_vk, None, None)

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

        # set fees
        fees = {'add_schema_250': 250*100000,
                'add_cred_def_125': 125*100000,
                'add_rrd_100': 100*100000,
                'add_rre_0_5': int(0.5*100000)}
        req = await payment.build_set_txn_fees_req(wallet_handler, trustee_did, libsovtoken_payment_method,
                                                   json.dumps(fees))
        req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
        req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
        res5 = json.loads(await ledger.submit_request(pool_handler, req))
        print(res5)
        assert res5['op'] == 'REPLY'

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
                                                               'metadata': {'fees': 'add_cred_def_125'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '2',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_cred_def_125'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_cred_def_125'}
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
                                                               'metadata': {'fees': 'add_rrd_100'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '2',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_rrd_100'}
                                                           },
                                                           {
                                                               'constraint_id': 'ROLE',
                                                               'role': '101',
                                                               'sig_count': 1,
                                                               'need_to_be_owner': False,
                                                               'metadata': {'fees': 'add_rrd_100'}
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
                                                       'metadata': {'fees': 'add_rre_0_5'}
                                                   }))
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res4)
        assert res4['op'] == 'REPLY'

        # send schema with fees
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, adder_did, address)
        res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, adder_did, req)
        source1 = \
            json.loads(await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res))[0]['source']
        # negative
        schema_id, schema_json = \
            await anoncreds.issuer_create_schema(io_did, random_string(5), '1.0', json.dumps(['name', 'age']))
        req = await ledger.build_schema_request(io_did, schema_json)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, io_did, req, json.dumps([source1]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': 750 * 100000}]), None)
        res = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, io_did, req_with_fees_json))
        print(res)
        assert res['op'] == 'REJECT'
        # positive
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
        # negative
        cred_def_id, cred_def_json = \
            await anoncreds.issuer_create_and_store_credential_def(wallet_handler, io_did, schema_json,
                                                                   random_string(5), None,
                                                                   json.dumps({'support_revocation': True}))
        req = await ledger.build_cred_def_request(io_did, cred_def_json)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, io_did, req, json.dumps([source2]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': 625 * 100000}]), None)
        res = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, io_did, req_with_fees_json))
        print(res)
        assert res['op'] == 'REJECT'
        # positive
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
        # negative
        revoc_reg_def_id, revoc_reg_def_json, revoc_reg_entry_json = \
            await anoncreds.issuer_create_and_store_revoc_reg(wallet_handler, io_did, None, random_string(5),
                                                              cred_def_id, json.dumps({'max_cred_num': 1,
                                                                                       'issuance_type':
                                                                                           'ISSUANCE_BY_DEFAULT'}),
                                                              tails_writer_handle)
        req = await ledger.build_revoc_reg_def_request(io_did, revoc_reg_def_json)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, io_did, req, json.dumps([source3]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': 525 * 100000}]), None)
        res = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, io_did, req_with_fees_json))
        print(res)
        assert res['op'] == 'REJECT'
        # positive
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
        # negative
        req = await ledger.build_revoc_reg_entry_request\
            (io_did, revoc_reg_def_id, 'CL_ACCUM', revoc_reg_entry_json)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, io_did, req, json.dumps([source4]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': int(524.5 * 100000)}]), None)
        res = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, io_did, req_with_fees_json))
        print(res)
        assert res['op'] == 'REJECT'
        # positive
        req = await ledger.build_revoc_reg_entry_request\
            (cd_adder_did, revoc_reg_def_id, 'CL_ACCUM', revoc_reg_entry_json)
        req_with_fees_json, _ = await payment.add_request_fees(wallet_handler, cd_adder_did, req, json.dumps([source4]),
                                                               json.dumps([{'recipient': address,
                                                                            'amount': int(524.5 * 100000)}]), None)
        res10 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, cd_adder_did, req_with_fees_json))
        print(res10)
        assert res10['op'] == 'REPLY'
