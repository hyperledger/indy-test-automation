import pytest
import asyncio
from system.utils import *
import docker


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

        for i in range(25):
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
            await ensure_pool_is_in_sync()
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
        await ensure_pool_is_in_sync()
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
        print(res4)
        assert res4['op'] == 'REPLY'

        # check again that pool is ok
        await ensure_pool_is_in_sync()
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)

    @pytest.mark.asyncio
    # ST-600 / ST-604
    async def test_get_utxo_pagination_and_state_proof(
            self, payment_init, pool_handler, wallet_handler, get_default_trustee
    ):
        hosts = [testinfra.get_host('docker://node' + str(i)) for i in range(1, 8)]
        libsovtoken_payment_method = 'sov'
        trustee_did, _ = get_default_trustee
        address0 = await payment.create_payment_address(
            wallet_handler, libsovtoken_payment_method, json.dumps({"seed": str('0000000000000000000000000Wallet0')})
        )
        try:
            trustee_did2, trustee_vk2 = await did.create_and_store_my_did(
                wallet_handler, json.dumps({"seed": str('000000000000000000000000Trustee2')})
            )
            trustee_did3, trustee_vk3 = await did.create_and_store_my_did(
                wallet_handler, json.dumps({"seed": str('000000000000000000000000Trustee3')})
            )
            await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did2, trustee_vk2, None, 'TRUSTEE')
            await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did3, trustee_vk3, None, 'TRUSTEE')
        except IndyError:
            trustee_did2, trustee_vk2 = 'LnXR1rPnncTPZvRdmJKhJQ', 'BnSWTUQmdYCewSGFrRUhT6LmKdcCcSzRGqWXMPnEP168'
            trustee_did3, trustee_vk3 = 'PNQm3CwyXbN5e39Rw3dXYx', 'DC8gEkb1cb4T9n3FcZghTkSp1cGJaZjhsPdxitcu6LUj'

        addresses = []
        outputs = []

        for i in range(3):
            addresses.append([])
            outputs.append([])
            for j in range(1500):
                address = await payment.create_payment_address(
                    wallet_handler, libsovtoken_payment_method, json.dumps({})
                )
                addresses[i].append(address)
                output = {"recipient": address, "amount": 1}
                outputs[i].append(output)

        for output in outputs:
            req, _ = await payment.build_mint_req(wallet_handler, trustee_did, json.dumps(output), None)
            req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
            req = await ledger.multi_sign_request(wallet_handler, trustee_did2, req)
            req = await ledger.multi_sign_request(wallet_handler, trustee_did3, req)
            res1 = json.loads(await ledger.submit_request(pool_handler, req))
            assert res1['op'] == 'REPLY'

        sources = []
        for address in itertools.chain(*addresses):
            req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address)
            res = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
            source = json.loads(
                await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res)
            )[0]['source']
            sources.append(source)

        for source in sources:
            req, _ = await payment.build_payment_req(
                wallet_handler, trustee_did, json.dumps([source]), json.dumps(
                    [{"recipient": address0, "amount": 1}]
                ), None
            )
            res = json.loads(await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req))
            assert res['op'] == 'REPLY'

        # default check
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address0)
        res1 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert json.loads(res1)['op'] == 'REPLY'
        source1 = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res1)
        )[0]['source']

        # default check with from - negative
        req, _ = await payment.build_get_payment_sources_with_from_request(wallet_handler, trustee_did, address0, -1501)
        res11 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert json.loads(res11)['op'] == 'REQNACK'

        # default check with from - positive
        req, _ = await payment.build_get_payment_sources_with_from_request(wallet_handler, trustee_did, address0, 1000)
        res111 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert json.loads(res111)['op'] == 'REPLY'
        source111 = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res111)
        )[0]['source']

        # check state proof reading
        outputs1 = [host.run('systemctl stop indy-node') for host in hosts[:-1]]
        req, _ = await payment.build_get_payment_sources_request(wallet_handler, trustee_did, address0)
        res2 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert json.loads(res2)['op'] == 'REPLY'
        source2 = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res2)
        )[0]['source']

        # check state proof reading with from - negative
        req, _ = await payment.build_get_payment_sources_with_from_request(wallet_handler, trustee_did, address0, -1501)
        with pytest.raises(IndyError):
            await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)

        req, _ = await payment.build_get_payment_sources_with_from_request(wallet_handler, trustee_did, address0, 1000)
        res22 = await ledger.sign_and_submit_request(pool_handler, wallet_handler, trustee_did, req)
        assert json.loads(res22)['op'] == 'REPLY'
        source22 = json.loads(
            await payment.parse_get_payment_sources_response(libsovtoken_payment_method, res22)
        )[0]['source']

        outputs2 = [host.run('systemctl start indy-node') for host in hosts[:-1]]
        print(outputs2)

        # check that pool is ok
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_is_in_sync()
        await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)
