import pytest
import asyncio
from system.utils import *
from random import randrange as rr
from datetime import datetime, timedelta, timezone


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestAuthMapMiscSuite:

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
    async def test_case_node(
            self, pool_handler, wallet_handler, get_default_trustee,
            adder_role, adder_role_num, editor_role, editor_role_num
    ):
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
    @pytest.mark.asyncio
    async def test_case_pool_restart(
            self, pool_handler, wallet_handler, get_default_trustee, adder_role, adder_role_num
    ):  # we can add pool restart only
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
    async def test_case_validator_info(
            self, pool_handler, wallet_handler, get_default_trustee, adder_role, adder_role_num
    ):  # we can add validator info only
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
    async def test_case_pool_config(
            self, pool_handler, wallet_handler, get_default_trustee, editor_role, editor_role_num
    ):  # we can edit pool config only
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
    async def test_case_auth_rule(
            self, pool_handler, wallet_handler, get_default_trustee, editor_role, editor_role_num
    ):  # we can edit auth rule only
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

    # TODO might make sense to move to separate module since other tests here
    # organized per txn type
    @pytest.mark.asyncio
    async def test_case_forbidden(self, pool_handler, wallet_handler, get_default_trustee):

        trustee_did, _ = get_default_trustee
        trustee_role, trustee_role_num = 'TRUSTEE', '0'

        logger.info("1 Adding new trustee to ledger")
        new_trustee_did, new_trustee_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, new_trustee_did, new_trustee_vk, None, trustee_role
        )
        assert res['op'] == 'REPLY'

        logger.info("2 Setting forbidden auth rule for adding trustees")
        req = await ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', trustee_role_num,
                                                   json.dumps({
                                                       'constraint_id': 'FORBIDDEN',
                                                   }))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        assert res['op'] == 'REPLY'

        logger.info("3 Getting newly set forbidden constraint")
        req = await ledger.build_get_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', trustee_role_num)
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        assert res['op'] == 'REPLY'
        assert res['result']['data'][0]['constraint']['constraint_id'] == 'FORBIDDEN'

        logger.info("4 Trying to add one more trustee")
        one_more_new_trustee_did, one_more_new_trustee_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, one_more_new_trustee_did, one_more_new_trustee_vk, None, trustee_role
        )
        assert res['op'] == 'REJECT'

    # TODO might make sense to move to separate module since other tests here
    # organized per txn type
    @pytest.mark.asyncio
    async def test_case_auth_rules(self, pool_handler, wallet_handler, get_default_trustee):

        trustee_did, _ = get_default_trustee
        trustee_role, trustee_role_num = 'TRUSTEE', '0'
        steward_role, steward_role_num = 'STEWARD', '2'

        logger.info("1 Creating new steward")
        steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, steward_role)
        assert res['op'] == 'REPLY'

        logger.info("2 Creating some new trustee")
        _new_trustee_did, _new_trustee_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(pool_handler, wallet_handler, trustee_did, _new_trustee_did, _new_trustee_vk, None, trustee_role)
        assert res['op'] == 'REPLY'

        logger.info("3 Trying to add new trustee using steward as submitter")
        new_trustee_did, new_trustee_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(
            pool_handler, wallet_handler, steward_did, new_trustee_did, new_trustee_vk, None, trustee_role
        )
        assert res['op'] == 'REJECT'

        logger.info("4 Trying to add new steward using steward as submitter")
        new_steward_did, new_steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(
            pool_handler, wallet_handler, steward_did, new_steward_did, new_steward_vk, None, trustee_role
        )
        assert res['op'] == 'REJECT'

        logger.info("5 Send auth rules txn to allow stewards to add new trustees and stewrds")
        one_steward_constraint = {
           'constraint_id': 'ROLE',
           'role': steward_role_num,
           'sig_count': 1,
           'need_to_be_owner': False,
           'metadata': {}
        }
        req = await ledger.build_auth_rules_request(trustee_did, json.dumps([
            {
                'auth_type': '1',
                'auth_action': 'ADD',
                'field': 'role',
                'old_value': '*',
                'new_value': trustee_role_num,
                'constraint': one_steward_constraint
            },
            {
                'auth_type': '1',
                'auth_action': 'ADD',
                'field': 'role',
                'old_value': '*',
                'new_value': steward_role_num,
                'constraint': one_steward_constraint
            },
        ]))
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        assert res['op'] == 'REPLY'

        logger.info("6 Getting recently set auth rules")
        for role_num in (trustee_role_num, steward_role_num):
            req = await ledger.build_get_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', role_num)
            res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
            assert res['op'] == 'REPLY'
            assert res['result']['data'][0]['constraint'] == one_steward_constraint

        logger.info("7 Trying to add new trustee using trustee as submitter")
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, new_trustee_did, new_trustee_vk, None, trustee_role
        )
        assert res['op'] == 'REJECT'

        logger.info("8 Trying to add new steward using trustee as submitter")
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, new_trustee_did, new_steward_vk, None, trustee_role
        )
        assert res['op'] == 'REJECT'

        logger.info("9 Adding new trustee using steward as submitter")
        new_trustee_did, new_trustee_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(
            pool_handler, wallet_handler, steward_did, new_trustee_did, new_trustee_vk, None, trustee_role
        )
        assert res['op'] == 'REPLY'

        logger.info("10 Adding new steward using steward as submitter")
        new_steward_did, new_steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        res = await send_nym(
            pool_handler, wallet_handler, steward_did, new_steward_did, new_steward_vk, None, trustee_role
        )
        assert res['op'] == 'REPLY'
