import pytest
import asyncio
from system.utils import *
from random import randrange as rr
from datetime import datetime, timedelta, timezone

from indy_vdr.error import VdrError, VdrErrorCode


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
        adder_did, adder_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['txnMetadata']['seqNo'] is not None
        # add editor to edit node
        editor_did, editor_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['txnMetadata']['seqNo'] is not None
        # set rule for adding
        req = ledger.build_auth_rule_request(trustee_did, '0', 'ADD', 'services', '*', str(['VALIDATOR']),
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert res2['txnMetadata']['seqNo'] is not None
        # set rule for editing
        req = ledger.build_auth_rule_request(trustee_did, '0', 'EDIT', 'services', str(['VALIDATOR']), str([]),
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res3 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert res3['txnMetadata']['seqNo'] is not None
        # add node
        alias = random_string(5)
        client_ip = '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255))
        client_port = rr(1, 32767)
        node_ip = '{}.{}.{}.{}'.format(rr(1, 255), 0, 0, rr(1, 255))
        node_port = rr(1, 32767)
        req = ledger.build_node_request(adder_did, adder_vk,  # adder_vk is used as node target did here
                                              json.dumps(
                                                   {
                                                       'alias': alias,
                                                       'client_ip': client_ip,
                                                       'client_port': client_port,
                                                       'node_ip': node_ip,
                                                       'node_port': node_port,
                                                       'services': ['VALIDATOR']
                                                   }))
        res4 = await sign_and_submit_request(pool_handler, wallet_handler, adder_did, req)
        assert res4['txnMetadata']['seqNo'] is not None
        # edit node
        req = ledger.build_node_request(editor_did, adder_vk,  # adder_vk is used as node target did here
                                              json.dumps(
                                                   {
                                                       'alias': alias,
                                                       'services': []
                                                   }))
        res5 = await sign_and_submit_request(pool_handler, wallet_handler, editor_did, req)
        assert res5['txnMetadata']['seqNo'] is not None

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
        adder_did, adder_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['txnMetadata']['seqNo'] is not None
        await asyncio.sleep(15)
        # set rule for adding
        req = ledger.build_auth_rule_request(trustee_did, '118', 'ADD', 'action', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert res2['txnMetadata']['seqNo'] is not None
        # restart pool
        req = ledger.build_pool_restart_request\
            (adder_did, 'start', datetime.strftime(datetime.now(tz=timezone.utc) + timedelta(minutes=60),
                                                   '%Y-%m-%dT%H:%M:%S%z'))
        res3 = await sign_and_submit_action(pool_handler, wallet_handler, adder_did, req)
        res3 = [json.loads(v) for k, v in res3.items()]
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
        adder_did, adder_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, adder_did, adder_vk, None, adder_role)
        assert res['txnMetadata']['seqNo'] is not None
        await asyncio.sleep(15)
        # set rule for adding
        req = ledger.build_auth_rule_request(trustee_did, '119', 'ADD', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': adder_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert res2['txnMetadata']['seqNo'] is not None
        req = ledger.build_get_validator_info_request(adder_did)
        res3 = await sign_and_submit_action(pool_handler, wallet_handler, adder_did, req)
        res3 = [json.loads(v) for k, v in res3.items()]
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
        editor_did, editor_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['txnMetadata']['seqNo'] is not None
        # set rule for editing
        req = ledger.build_auth_rule_request(trustee_did, '111', 'EDIT', 'action', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert res2['txnMetadata']['seqNo'] is not None
        req = ledger.build_pool_config_request(editor_did, False, False)
        res3 = await sign_and_submit_request(pool_handler, wallet_handler, editor_did, req)
        assert res3['txnMetadata']['seqNo'] is not None

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
        editor_did, editor_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, editor_did, editor_vk, None, editor_role)
        assert res['txnMetadata']['seqNo'] is not None
        # set rule for editing
        req = ledger.build_auth_rule_request(trustee_did, '120', 'EDIT', '*', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': editor_role_num,
                                                       'sig_count': 1,
                                                       'need_to_be_owner': False,
                                                       'metadata': {}
                                                   }))
        res2 = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert res2['txnMetadata']['seqNo'] is not None
        await asyncio.sleep(15)
        req = ledger.build_auth_rule_request(editor_did, '111', 'EDIT', 'action', '*', '*',
                                                   json.dumps({
                                                       'constraint_id': 'ROLE',
                                                       'role': '*',
                                                       'sig_count': 5,
                                                       'need_to_be_owner': True,
                                                       'metadata': {}
                                                   }))
        res3 = await sign_and_submit_request(pool_handler, wallet_handler, editor_did, req)
        assert res3['txnMetadata']['seqNo'] is not None

    # TODO might make sense to move to separate module since other tests here
    # organized per txn type
    @pytest.mark.asyncio
    async def test_case_forbidden(self, pool_handler, wallet_handler, get_default_trustee):

        trustee_did, _ = get_default_trustee
        trustee_role, trustee_role_num = 'TRUSTEE', '0'

        logger.info("1 Adding new trustee to ledger")
        new_trustee_did, new_trustee_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, new_trustee_did, new_trustee_vk, None, trustee_role
        )
        assert res['txnMetadata']['seqNo'] is not None

        logger.info("2 Setting forbidden auth rule for adding trustees")
        req = ledger.build_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', trustee_role_num,
                                                   json.dumps({
                                                       'constraint_id': 'FORBIDDEN',
                                                   }))
        res = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert res['txnMetadata']['seqNo'] is not None

        logger.info("3 Getting newly set forbidden constraint")
        req = ledger.build_get_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', trustee_role_num)
        res = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)

        # FIXME ['seqNo'] is None in response
        # assert res['seqNo'] is not None

        assert res['data'][0]['constraint']['constraint_id'] == 'FORBIDDEN'

        logger.info("4 Trying to add one more trustee")
        one_more_new_trustee_did, one_more_new_trustee_vk = await create_and_store_did(wallet_handler)
        with pytest.raises(VdrError) as exp_err:
            await send_nym(
            pool_handler, wallet_handler, trustee_did, one_more_new_trustee_did, one_more_new_trustee_vk, None, trustee_role
        )
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED

    # TODO might make sense to move to separate module since other tests here
    # organized per txn type
    @pytest.mark.asyncio
    async def test_case_auth_rules(self, pool_handler, wallet_handler, get_default_trustee):

        trustee_did, _ = get_default_trustee
        trustee_role, trustee_role_num = 'TRUSTEE', '0'
        steward_role, steward_role_num = 'STEWARD', '2'

        logger.info("1 Creating new steward")
        steward_did, steward_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, None, steward_role)
        assert res['txnMetadata']['seqNo'] is not None

        logger.info("2 Creating some new trustee")
        _new_trustee_did, _new_trustee_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(pool_handler, wallet_handler, trustee_did, _new_trustee_did, _new_trustee_vk, None, trustee_role)
        assert res['txnMetadata']['seqNo'] is not None

        logger.info("3 Trying to add new trustee using steward as submitter")
        new_trustee_did, new_trustee_vk = await create_and_store_did(wallet_handler)
        with pytest.raises(VdrError) as exp_err:
            await send_nym(
            pool_handler, wallet_handler, steward_did, new_trustee_did, new_trustee_vk, None, trustee_role
        )
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED

        logger.info("4 Trying to add new steward using steward as submitter")
        new_steward_did, new_steward_vk = await create_and_store_did(wallet_handler)
        with pytest.raises(VdrError) as exp_err:
            await send_nym(
            pool_handler, wallet_handler, steward_did, new_steward_did, new_steward_vk, None, trustee_role
        )
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED

        logger.info("5 Send auth rules txn to allow stewards to add new trustees and stewrds")
        one_steward_constraint = {
           'constraint_id': 'ROLE',
           'role': steward_role_num,
           'sig_count': 1,
           'need_to_be_owner': False,
           'metadata': {}
        }
        req = ledger.build_auth_rules_request(trustee_did, json.dumps([
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
        res = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert res['txnMetadata']['seqNo'] is not None

        logger.info("6 Getting recently set auth rules")
        for role_num in (trustee_role_num, steward_role_num):
            req = ledger.build_get_auth_rule_request(trustee_did, '1', 'ADD', 'role', '*', role_num)
            res = await sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
            # FIXME ['seqNo'] is None in response
            # assert res['seqNo'] is not None
            assert res['data'][0]['constraint'] == one_steward_constraint

        logger.info("7 Trying to add new trustee using trustee as submitter")
        with pytest.raises(VdrError) as exp_err:
            await send_nym(
            pool_handler, wallet_handler, trustee_did, new_trustee_did, new_trustee_vk, None, trustee_role
        )
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED

        logger.info("8 Trying to add new steward using trustee as submitter")
        with pytest.raises(VdrError) as exp_err:
            await send_nym(
            pool_handler, wallet_handler, trustee_did, new_trustee_did, new_steward_vk, None, trustee_role
        )
        assert exp_err.value.code == VdrErrorCode.POOL_REQUEST_FAILED

        logger.info("9 Adding new trustee using steward as submitter")
        new_trustee_did, new_trustee_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(
            pool_handler, wallet_handler, steward_did, new_trustee_did, new_trustee_vk, None, trustee_role
        )
        assert res['txnMetadata']['seqNo'] is not None

        logger.info("10 Adding new steward using steward as submitter")
        new_steward_did, new_steward_vk = await create_and_store_did(wallet_handler)
        res = await send_nym(
            pool_handler, wallet_handler, steward_did, new_steward_did, new_steward_vk, None, trustee_role
        )
        assert res['txnMetadata']['seqNo'] is not None
