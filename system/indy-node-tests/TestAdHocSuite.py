import pytest
from system.utils import *
import docker
from random import choice


@pytest.mark.usefixtures('docker_setup_and_teardown')
@pytest.mark.usefixtures('check_no_failures_fixture')
class TestAdHocSuite:

    @pytest.mark.nodes_num(4)
    @pytest.mark.asyncio
    # staging net issue (INDY-2233)
    async def test_rotate_bls_and_get_txn(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        docker_client = docker.from_env()
        trustee_did, _ = get_default_trustee
        steward_did, steward_vk = await did.create_and_store_my_did(
            wallet_handler, json.dumps({'seed': '000000000000000000000000Steward4'})
        )
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=3)

        for i in range(10):
            # rotate bls keys for Node4
            res1 = docker_client.containers.list(
                filters={'name': 'node4'}
            )[0].exec_run(
                ['init_bls_keys', '--name', 'Node4'], user='indy'
            )
            bls_key, bls_key_pop = res1.output.decode().splitlines()
            bls_key, bls_key_pop = bls_key.split()[-1], bls_key_pop.split()[-1]
            data = json.dumps(
                {
                    'alias': 'Node4',
                    'blskey': bls_key,
                    'blskey_pop': bls_key_pop
                }
            )
            req = await ledger.build_node_request(steward_did, '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA', data)
            res2 = json.loads(
                await ledger.sign_and_submit_request(pool_handler, wallet_handler, steward_did, req)
            )
            assert res2['op'] == 'REPLY'

            # write txn
            await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did)

            # get txn
            req = await ledger.build_get_txn_request(None, 'DOMAIN', 10)
            res3 = json.loads(await ledger.submit_request(pool_handler, req))
            assert res3['result']['seqNo'] is not None

            # check that pool is ok
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
            await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
            await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.asyncio
    # SN-7
    async def test_drop_states(
            self, payment_init, pool_handler, wallet_handler, get_default_trustee,
            initial_token_minting, initial_fees_setting
    ):
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        address2 = await payment.create_payment_address(wallet_handler, libsovtoken_payment_method, '{}')

        # mint tokens
        address = initial_token_minting

        # set fees
        print(initial_fees_setting)

        # set auth rule for schema
        req = await ledger.build_auth_rule_request(trustee_did, '101', 'ADD', '*', None, '*',
                                                   json.dumps(
                                                    {
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
                                                    }
                                                        )
                                                   )
        res1 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res1)
        assert res1['op'] == 'REPLY'

        # write schema with fees
        source1, _ = await get_payment_sources(pool_handler, wallet_handler, address)
        schema_id, schema_json = await anoncreds.issuer_create_schema(
            trustee_did, random_string(5), '1.0', json.dumps(['name', 'age'])
        )
        req = await ledger.build_schema_request(trustee_did, schema_json)
        req_with_fees_json, _ = await payment.add_request_fees(
            wallet_handler, trustee_did, req, json.dumps([source1]), json.dumps(
                [{'recipient': address, 'amount': 750 * 100000}]
            ), None
        )
        res2 = json.loads(
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req_with_fees_json)
        )
        print(res2)
        assert res2['op'] == 'REPLY'

        # send payment
        source2, _ = await get_payment_sources(pool_handler, wallet_handler, address)
        req, _ = await payment.build_payment_req(
            wallet_handler, trustee_did, json.dumps([source2]), json.dumps(
                [{"recipient": address2, "amount": 500 * 100000}, {"recipient": address, "amount": 250 * 100000}]
            ), None
        )
        res3 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        print(res3)
        assert res3['op'] == 'REPLY'

        # stop Node7 -> drop token state -> start Node7
        node7 = NodeHost(7)
        node7.stop_service()
        time.sleep(3)
        for _ledger in ['pool', 'domain', 'config', 'sovtoken']:
            print(node7.run('rm -rf /var/lib/indy/sandbox/data/Node7/{}_state'.format(_ledger)))
        time.sleep(3)
        node7.start_service()

        # check that pool is ok
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # write some txns
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=10)

        # send another payment
        source3, _ = await get_payment_sources(pool_handler, wallet_handler, address)
        req, _ = await payment.build_payment_req(
            wallet_handler, trustee_did, json.dumps([source3]), json.dumps(
                [{"recipient": address2, "amount": 125 * 100000}, {"recipient": address, "amount": 125 * 100000}]
            ), None
        )
        res4 = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
        assert res4['op'] == 'REPLY'

        # check again that pool is ok
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize(
        'demote_count, promote_count',
        [
            (1, 5),
            (100, 5),
            (100, 1)
        ]
    )
    @pytest.mark.asyncio
    async def test_misc_redundant_demotions_promotions(
            self, pool_handler, wallet_handler, get_default_trustee, payment_init, initial_token_minting, nodes_num,
            demote_count, promote_count
    ):
        trustee_did, _ = get_default_trustee
        pool_info = get_pool_info('1')
        node_list = ['Node{}'.format(x) for x in range(1, nodes_num + 1)]
        address = initial_token_minting
        fees = await fees_setter(pool_handler, wallet_handler, trustee_did, 'sov')

        # find primary
        primary, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        # select random node
        node_to_demote = choice(node_list)
        # demote it
        demote_tasks = []
        for i in range(demote_count):
            task = demote_node(pool_handler, wallet_handler, trustee_did, node_to_demote, pool_info[node_to_demote])
            demote_tasks.append(task)
        await asyncio.gather(*demote_tasks, return_exceptions=True)
        await pool.refresh_pool_ledger(pool_handler)
        # make sure VC is done
        new_primary = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
        new_primary_name = 'Node{}'.format(new_primary)
        # demote new primary
        demote_tasks = []
        for i in range(demote_count):
            task = demote_node(
                pool_handler, wallet_handler, trustee_did, new_primary_name, pool_info[new_primary_name]
            )
            demote_tasks.append(task)
        await asyncio.gather(*demote_tasks, return_exceptions=True)
        await pool.refresh_pool_ledger(pool_handler)
        # make sure VC is done
        super_new_primary = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, new_primary)
        # write txn with fees
        req = await ledger.build_attrib_request(trustee_did, trustee_did, None, None, random_string(256))
        await add_fees_and_send_request(pool_handler, wallet_handler, trustee_did, address, req, fees['attrib'])
        # promote both nodes back simultaneously
        promote_tasks = []
        for i in range(promote_count):
            task1 = promote_node(pool_handler, wallet_handler, trustee_did, node_to_demote, pool_info[node_to_demote])
            promote_tasks.append(task1)
            task2 = promote_node(
                pool_handler, wallet_handler, trustee_did, new_primary_name, pool_info[new_primary_name]
            )
            promote_tasks.append(task2)
        await asyncio.gather(*promote_tasks, return_exceptions=True)
        await pool.refresh_pool_ledger(pool_handler)
        # make sure VC is done
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, super_new_primary)

        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=10)
        await ensure_pool_is_okay(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.parametrize(
        'iterations, nyms_count',
        [
            (1, 10),
            (5, 10),
            (5, 1)
        ]
    )
    @pytest.mark.asyncio
    async def test_misc_cyclic_demotions_promotions(
            self, pool_handler, wallet_handler, get_default_trustee, payment_init, initial_token_minting, nodes_num,
            iterations, nyms_count
    ):
        trustee_did, _ = get_default_trustee
        pool_info = get_pool_info('1')
        node_list = ['Node{}'.format(x) for x in range(1, nodes_num + 1)]
        address = initial_token_minting
        fees = await fees_setter(pool_handler, wallet_handler, trustee_did, 'sov')

        for _ in range(iterations):
            # find primary
            primary, primary_alias, primary_did = await get_primary(pool_handler, wallet_handler, trustee_did)
            # select random node
            node_to_demote = choice(node_list)
            # demote it
            await demote_node(pool_handler, wallet_handler, trustee_did, node_to_demote, pool_info[node_to_demote])
            await pool.refresh_pool_ledger(pool_handler)
            # make sure VC is done
            new_primary = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary)
            # make sure pool works
            await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=nyms_count)
            # write txn with fees
            req = await ledger.build_attrib_request(trustee_did, trustee_did, None, None, random_string(256))
            await add_fees_and_send_request(pool_handler, wallet_handler, trustee_did, address, req, fees['attrib'])
            # promote node back
            await promote_node(pool_handler, wallet_handler, trustee_did, node_to_demote, pool_info[node_to_demote])
            await pool.refresh_pool_ledger(pool_handler)
            # make sure VC is done
            await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, new_primary)
            # make sure pool works
            await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=nyms_count)

        await ensure_pool_is_okay(pool_handler, wallet_handler, trustee_did)
