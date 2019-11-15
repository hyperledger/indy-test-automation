import pytest
import asyncio
from system.utils import *
from async_generator import async_generator, yield_


# setup once for all cases
@pytest.fixture(scope='module', autouse=True)
@async_generator
async def docker_setup_and_teardown(docker_setup_and_teardown_module):
    await yield_()


# TODO IMPLEMENT AND PARAMETRIZE ALL POSITIVE AND NEGATIVE CASES
@pytest.mark.usefixtures('check_no_failures_fixture')
class TestLedgerSuite:

    @pytest.mark.parametrize('target_role', ['TRUSTEE', 'STEWARD', 'ENDORSER', 'NETWORK_MONITOR', None])
    @pytest.mark.parametrize('alias', [None, random_string(1), random_string(256)])
    @pytest.mark.asyncio
    # NYM						GET_NYM
    async def test_nym(
            self, pool_handler, wallet_handler, get_default_trustee, target_role, alias
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        # --------------------------------------------------------------------------------------------------------------
        res = await send_nym(
            pool_handler, wallet_handler, trustee_did, target_did, target_vk, alias, target_role
        )
        assert res['op'] == 'REPLY'

        await ensure_get_something(get_nym, pool_handler, wallet_handler, trustee_did, target_did)

    @pytest.mark.parametrize('target_role', ['TRUSTEE', 'STEWARD', 'ENDORSER', 'NETWORK_MONITOR', None])
    @pytest.mark.parametrize(
        'xhash, raw, enc, raw_key',
        [
            (hashlib.sha256().hexdigest(), None, None, None),
            (None, json.dumps({'key': random_string(256)}), None, 'key'),
            (None, None, random_string(256), None)
        ]
    )
    @pytest.mark.asyncio
    # ATTRIB					GET_ATTRIB
    async def test_attrib(
            self, pool_handler, wallet_handler, get_default_trustee, target_role, xhash, raw, enc, raw_key
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        await send_nym(
            pool_handler, wallet_handler, trustee_did, target_did, target_vk, random_string(256), target_role
        )
        # --------------------------------------------------------------------------------------------------------------
        res = await send_attrib(pool_handler, wallet_handler, target_did, target_did, xhash, raw, enc)
        assert res['op'] == 'REPLY'

        await ensure_get_something(
            get_attrib, pool_handler, wallet_handler, trustee_did, target_did, xhash, raw_key, enc
        )

    @pytest.mark.parametrize('target_role', ['TRUSTEE', 'STEWARD', 'ENDORSER'])
    @pytest.mark.parametrize('name', [random_string(1), random_string(256)])
    @pytest.mark.asyncio
    # SCHEMA					GET_SCHEMA + PARSE_GET_SCHEMA
    async def test_schema(
            self, pool_handler, wallet_handler, get_default_trustee, target_role, name
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        await send_nym(
            pool_handler, wallet_handler, trustee_did, target_did, target_vk, random_string(256), target_role
        )
        # --------------------------------------------------------------------------------------------------------------
        schema_id_local, res1 = await send_schema(
            pool_handler, wallet_handler, target_did, name, '1.0', json.dumps(
                [random_string(1), random_string(256)]
            )
        )
        assert res1['op'] == 'REPLY'

        res2 = await ensure_get_something(get_schema, pool_handler, wallet_handler, trustee_did, schema_id_local)

        schema_id_ledger, schema_json = await ledger.parse_get_schema_response(json.dumps(res2))
        assert schema_id_local == schema_id_ledger
        assert res2['result']['seqNo'] == json.loads(schema_json)['seqNo']

    @pytest.mark.parametrize('target_role', ['TRUSTEE', 'STEWARD', 'ENDORSER'])
    @pytest.mark.parametrize('tag', [random_string(1), random_string(256)])
    @pytest.mark.parametrize('revocation', [False, True])
    @pytest.mark.asyncio
    # CRED_DEF				    GET_CRED_DEF + PARSE_GET_CRED_DEF
    async def test_cred_def(
            self, pool_handler, wallet_handler, get_default_trustee, target_role, tag, revocation
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        await send_nym(
            pool_handler, wallet_handler, trustee_did, target_did, target_vk, random_string(256), target_role
        )
        schema_id_local, res1 = await send_schema(
            pool_handler, wallet_handler, target_did, random_string(256), '1.0', json.dumps(
                [random_string(1), random_string(256)]
            )
        )
        assert res1['op'] == 'REPLY'
        res2 = await ensure_get_something(get_schema, pool_handler, wallet_handler, trustee_did, schema_id_local)
        schema_id_ledger, schema_json = await ledger.parse_get_schema_response(json.dumps(res2))
        # --------------------------------------------------------------------------------------------------------------
        cred_def_id_local, _, res3 = await send_cred_def(
            pool_handler, wallet_handler, target_did, schema_json, tag, None, json.dumps(
                {'support_revocation': revocation}
            )
        )

        res4 = await ensure_get_something(get_cred_def, pool_handler, wallet_handler, trustee_did, cred_def_id_local)

        cred_def_id_ledger, cred_def_json = await ledger.parse_get_cred_def_response(json.dumps(res4))
        assert cred_def_id_local == cred_def_id_ledger

    @pytest.mark.parametrize('target_role', ['TRUSTEE', 'STEWARD', 'ENDORSER'])
    @pytest.mark.parametrize('tag', [random_string(1), random_string(256)])
    @pytest.mark.parametrize('max_cred_num', [1, 4096, 65536])
    @pytest.mark.parametrize('issuance_type', ['ISSUANCE_BY_DEFAULT', 'ISSUANCE_ON_DEMAND'])
    @pytest.mark.asyncio
    # REV_REG_DEF				GET_REV_REG_DEF + PARSE_GET_REV_REG_DEF
    async def test_rev_reg_def(
            self, pool_handler, wallet_handler, get_default_trustee, target_role, tag, max_cred_num, issuance_type
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        await send_nym(
            pool_handler, wallet_handler, trustee_did, target_did, target_vk, random_string(256), target_role
        )
        schema_id_local, res1 = await send_schema(
            pool_handler, wallet_handler, target_did, random_string(256), '1.0', json.dumps(
                [random_string(1), random_string(256)]
            )
        )
        assert res1['op'] == 'REPLY'
        res2 = await ensure_get_something(get_schema, pool_handler, wallet_handler, trustee_did, schema_id_local)
        schema_id_ledger, schema_json = await ledger.parse_get_schema_response(json.dumps(res2))
        cred_def_id, _, res3 = await send_cred_def(
            pool_handler, wallet_handler, target_did, schema_json, random_string(256), None, json.dumps(
                {'support_revocation': True}
            )
        )
        # --------------------------------------------------------------------------------------------------------------
        rev_reg_def_id_local, rev_reg_def_json, rev_reg_entry_json, res4 = await send_revoc_reg_def(
            pool_handler, wallet_handler, target_did, None, tag, cred_def_id, json.dumps(
                {'max_cred_num': max_cred_num, 'issuance_type': issuance_type}
            )
        )

        res5 = await ensure_get_something(
            get_revoc_reg_def, pool_handler, wallet_handler, trustee_did, rev_reg_def_id_local
        )

        rev_reg_def_id_ledger, rev_reg_def_json = await ledger.parse_get_revoc_reg_def_response(json.dumps(res5))
        assert rev_reg_def_id_local == rev_reg_def_id_ledger

    @pytest.mark.parametrize('target_role', ['TRUSTEE', 'STEWARD', 'ENDORSER'])
    @pytest.mark.parametrize('tag', [random_string(1), random_string(256)])
    @pytest.mark.parametrize('max_cred_num', [1, 1024])
    @pytest.mark.parametrize('issuance_type', ['ISSUANCE_BY_DEFAULT', 'ISSUANCE_ON_DEMAND'])
    @pytest.mark.asyncio
    # REV_REG_ENTRY			    GET_REV_REG + PARSE_GET_REV_REG | GET_REV_REG_DELTA + PARSE_GET_REV_REG_DELTA
    async def test_rev_reg_entry(
            self, pool_handler, wallet_handler, get_default_trustee, target_role, tag, max_cred_num, issuance_type
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        timestamp0 = int(time.time())
        trustee_did, _ = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        await send_nym(
            pool_handler, wallet_handler, trustee_did, target_did, target_vk, random_string(256), target_role
        )
        schema_id_local, res1 = await send_schema(
            pool_handler, wallet_handler, target_did, random_string(256), '1.0', json.dumps(
                [random_string(1), random_string(256)]
            )
        )
        assert res1['op'] == 'REPLY'
        res2 = await ensure_get_something(get_schema, pool_handler, wallet_handler, trustee_did, schema_id_local)
        schema_id_ledger, schema_json = await ledger.parse_get_schema_response(json.dumps(res2))
        cred_def_id, _, res3 = await send_cred_def(
            pool_handler, wallet_handler, target_did, schema_json, random_string(256), None, json.dumps(
                {'support_revocation': True}
            )
        )
        # --------------------------------------------------------------------------------------------------------------
        rev_reg_def_id_local, rev_reg_def_json, rev_reg_entry_json, res4 = await send_revoc_reg_entry(
            pool_handler, wallet_handler, target_did, 'CL_ACCUM', tag, cred_def_id, json.dumps(
                {'max_cred_num': max_cred_num, 'issuance_type': issuance_type}
            )
        )

        timestamp1 = int(time.time())

        res5 = await ensure_get_something(
            get_revoc_reg, pool_handler, wallet_handler, trustee_did, rev_reg_def_id_local, timestamp1
        )

        res6 = await ensure_get_something(
            get_revoc_reg_delta, pool_handler, wallet_handler, trustee_did, rev_reg_def_id_local, timestamp0, timestamp1
        )

        rev_reg_def_id_ledger, rev_reg_json, timestamp2 = await ledger.parse_get_revoc_reg_response(
            json.dumps(res5)
        )
        assert rev_reg_def_id_local == rev_reg_def_id_ledger

        rev_reg_def_id_ledger, rev_reg_delta_json, timestamp3 = await ledger.parse_get_revoc_reg_delta_response(
            json.dumps(res6)
        )
        assert rev_reg_def_id_local == rev_reg_def_id_ledger

        assert rev_reg_json == rev_reg_delta_json  # is it ok?
        assert timestamp2 == timestamp3  # is it ok?

    @pytest.mark.parametrize(
        'txn_type, action, field, old_value, new_value, role, sig_count, need_to_be_owner',
        [
            ('101', 'ADD', '*', None, '*', '201', 2, True),
            ('102', 'EDIT', '*', '*', '*', '201', 3, False)
        ]
    )
    @pytest.mark.asyncio
    # AUTH_RULE				    GET_AUTH_RULE
    async def test_auth_rule(
            self, pool_handler, wallet_handler, get_default_trustee,
            txn_type, action, field, old_value, new_value, role, sig_count, need_to_be_owner
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        # --------------------------------------------------------------------------------------------------------------
        constraint = {
                        'constraint_id': 'ROLE',
                        'role': role,
                        'sig_count': sig_count,
                        'need_to_be_owner': need_to_be_owner,
                        'metadata': {}
                     }
        req1 = await ledger.build_auth_rule_request(
            trustee_did, txn_type, action, field, old_value, new_value, json.dumps(constraint)
        )
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req1))
        assert res1['op'] == 'REPLY'

        req2 = await ledger.build_get_auth_rule_request(trustee_did, txn_type, action, field, old_value, new_value)
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req2))
        assert res2['result']['data'][0]['constraint'] == constraint

    @pytest.mark.parametrize('ledger_type', ['DOMAIN', 'POOL', 'CONFIG', '1001'])
    @pytest.mark.parametrize('seqno', [1, 5])
    @pytest.mark.asyncio
    # 						    GET_TXN
    async def test_get_txn(
            self, pool_handler, wallet_handler, get_default_trustee, initial_token_minting, initial_fees_setting,
            payment_init, ledger_type, seqno
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        initial_token_minting
        initial_fees_setting
        # --------------------------------------------------------------------------------------------------------------
        req = await ledger.build_get_txn_request(trustee_did, ledger_type, seqno)
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        assert res['result']['seqNo'] is not None

    @pytest.mark.parametrize('target_role', ['TRUSTEE', 'STEWARD', 'NETWORK_MONITOR'])
    @pytest.mark.asyncio
    # 						    GET_VALIDATOR_INFO
    async def test_get_validator_info(
            self, pool_handler, wallet_handler, get_default_trustee, target_role
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        await send_nym(
            pool_handler, wallet_handler, trustee_did, target_did, target_vk, random_string(256), target_role
        )
        # --------------------------------------------------------------------------------------------------------------
        req = await ledger.build_get_validator_info_request(target_did)
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, req))
        res = {k: json.loads(v) for k, v in res.items()}
        assert all([v['op'] == 'REPLY' for k, v in res.items()])

    @pytest.mark.parametrize('writes', [False, True])
    @pytest.mark.parametrize('force', [False, True])
    @pytest.mark.asyncio
    # POOL_CONFIG
    async def test_pool_config(
            self, pool_handler, wallet_handler, get_default_trustee, writes, force
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        # --------------------------------------------------------------------------------------------------------------
        req = await ledger.build_pool_config_request(trustee_did, writes, force)
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        assert res['op'] == 'REPLY'

    @pytest.mark.parametrize('action', ['start', 'cancel'])
    @pytest.mark.parametrize('_datetime', ['2020-01-01T00:00:00.000000+00:00', ''])
    @pytest.mark.asyncio
    # POOL_RESTART
    async def test_pool_restart(
            self, pool_handler, wallet_handler, get_default_trustee, action, _datetime
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        # --------------------------------------------------------------------------------------------------------------
        req = await ledger.build_pool_restart_request(trustee_did, action, _datetime)
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        res = {k: json.loads(v) for k, v in res.items()}
        assert all([v['op'] == 'REPLY' for k, v in res.items()])

    @pytest.mark.parametrize('timeout', [5, 3600])
    @pytest.mark.parametrize('justification', [None, random_string(1), random_string(1000)])
    @pytest.mark.parametrize('reinstall', [False, True])
    @pytest.mark.parametrize('force', [False, True])
    @pytest.mark.parametrize('package', ['indy-node', 'sovrin'])
    @pytest.mark.asyncio
    # POOL_UPGRADE
    async def test_pool_upgrade(
            self, pool_handler, wallet_handler, get_default_trustee, timeout, justification, reinstall, force, package
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        dests = [
            'Gw6pDLhcBcoQesN72qfotTgFa7cbuqZpkX3Xo6pLhPhv', '8ECVSk179mjsjKRLWiQtssMLgp6EPhWXtaYyStWPSGAb',
            'DKVxG2fXXTU8yT5N7hGEbXB3dfdAnYv1JczDUHpmDxya', '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA',
            '4SWokCJWJc69Tn74VvLS6t2G2ucvXqM9FDMsWJjmsUxe', 'Cv1Ehj43DDM5ttNBmC6VPpEfwXWwfGktHwjDJsTV5Fz8',
            'BM8dTooz5uykCbYSAAFwKNkYfT4koomBHsSWHTDtkjhW'
        ]
        docker_7_schedule = json.dumps(
            dict(
                {
                    dest: datetime.strftime(
                        datetime.now(tz=timezone.utc) + timedelta(minutes=999 + i * 5), '%Y-%m-%dT%H:%M:%S%z'
                    ) for dest, i in zip(dests, range(len(dests)))
                }
            )
        )
        name = random_string(256)  # should be the same for start and cancel
        # --------------------------------------------------------------------------------------------------------------
        req1 = await ledger.build_pool_upgrade_request(
            trustee_did,
            name,
            '9.9.999',
            'start',
            hashlib.sha256().hexdigest(),
            timeout,
            docker_7_schedule,
            justification,
            reinstall,
            force,
            package
        )
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req1))
        print(res1)
        assert res1['op'] == 'REPLY'

        req2 = await ledger.build_pool_upgrade_request(
            trustee_did,
            name,
            '9.9.999',
            'cancel',
            hashlib.sha256().hexdigest(),
            timeout,
            docker_7_schedule,
            justification,
            reinstall,
            force,
            package
        )
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req2))
        print(res2)
        assert res2['op'] == 'REPLY'

    @pytest.mark.parametrize('alias_length', [1, 256])
    @pytest.mark.parametrize('services', [[], ['VALIDATOR']])
    @pytest.mark.asyncio
    # NODE
    async def test_node(
            self, pool_handler, wallet_handler, get_default_trustee, alias_length, services
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        target_did, target_vk = await did.create_and_store_my_did(wallet_handler, '{}')
        await send_nym(
            pool_handler, wallet_handler, trustee_did, target_did, target_vk, random_string(256), 'STEWARD'
        )
        # --------------------------------------------------------------------------------------------------------------
        req = await ledger.build_node_request(
            target_did, target_vk, json.dumps(
                {
                    'alias': random_string(alias_length),
                    'client_ip': '{}.{}.{}.{}'.format(
                        randrange(1, 255), randrange(1, 255), randrange(1, 255), randrange(1, 255)
                    ),
                    'client_port': randrange(1, 32767),
                    'node_ip': '{}.{}.{}.{}'.format(
                        randrange(1, 255), randrange(1, 255), randrange(1, 255), randrange(1, 255)
                    ),
                    'node_port': randrange(1, 32767),
                    'services': services
                }
            )
        )
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, target_did, req))
        print(res)
        assert res['op'] == 'REPLY'

    @pytest.mark.parametrize('key', [random_string(1), random_string(1024), random_string(4096)])
    @pytest.mark.parametrize('value', [random_string(1), random_string(1024), random_string(4096)])
    @pytest.mark.parametrize('context', [random_string(1), random_string(1024), random_string(4096)])
    @pytest.mark.parametrize('version_length', [2, 256])  # must be generated inside the test and started from 2
    @pytest.mark.asyncio
    # AML						GET_AML
    async def test_aml(
            self, pool_handler, wallet_handler, get_default_trustee, key, value, context, version_length
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        # --------------------------------------------------------------------------------------------------------------
        aml = {
            key: value
        }
        version = random_string(version_length)
        req1 = await ledger.build_acceptance_mechanisms_request(trustee_did, json.dumps(aml), version, context)
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req1))
        print(res1)
        assert res1['op'] == 'REPLY'

        for _timestamp, _version in [(None, None), (int(time.time()), None), (None, version)]:
            req2 = await ledger.build_get_acceptance_mechanisms_request(trustee_did, _timestamp, _version)
            res2 = json.loads(await ledger.submit_request(pool_handler, req2))
            assert res2['result']['seqNo'] is not None

    @pytest.mark.parametrize('text', [random_string(1), random_string(1024), random_string(4096)])
    @pytest.mark.parametrize('version_length', [2, 256])  # must be generated inside the test and started from 2
    @pytest.mark.asyncio
    # TAA						GET_TAA
    async def test_taa(
            self, pool_handler, wallet_handler, get_default_trustee, text, version_length
    ):
        # SETUP---------------------------------------------------------------------------------------------------------
        trustee_did, _ = get_default_trustee
        req = await ledger.build_acceptance_mechanisms_request(
            trustee_did, json.dumps({random_string(16): random_string(128)}), random_string(256), random_string(1024)
        )
        res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        assert res['op'] == 'REPLY'
        # --------------------------------------------------------------------------------------------------------------
        req1 = await ledger.build_txn_author_agreement_request(trustee_did, text, random_string(version_length))
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req1))
        print(res1)
        assert res1['op'] == 'REPLY'

        req2 = await ledger.build_get_txn_author_agreement_request(trustee_did, None)
        res2 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req2))
        assert res2['result']['seqNo'] is not None
