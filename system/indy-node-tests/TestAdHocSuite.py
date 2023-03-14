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
        steward_did, steward_vk = await create_and_store_did(
            wallet_handler, seed='000000000000000000000000Steward4'
        )
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=3)

        for i in range(10):
            # rotate bls keys for Node4
            res1 = docker_client.containers.list(
                filters={'name': 'node4'}
            )[0].exec_run(
                ['init_bls_keys', '--name', 'Node4'], user='indy'
            )

            bls_key, bls_key_pop = list(filter(lambda k: 'key is' in k, res1.output.decode().splitlines()))
            bls_key, bls_key_pop = bls_key.split()[-1], bls_key_pop.split()[-1]
            data = json.dumps(
                {
                    'alias': 'Node4',
                    'blskey': bls_key,
                    'blskey_pop': bls_key_pop
                }
            )
            req = ledger.build_node_request(steward_did, '4PS3EDQ3dW1tci1Bp6543CfuuebjFrg36kLAUcskGfaA', data)
            res2 = await sign_and_submit_request(pool_handler, wallet_handler, steward_did, req)

            # assert res2['op'] == 'REPLY'
            assert res2['txnMetadata']['seqNo'] is not None

            # write txn
            await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did)

            # get txn
            req = ledger.build_get_txn_request(None, 'DOMAIN', 10)
            res3 = await pool_handler.submit_request(req)
            assert res3['seqNo'] is not None

            # check that pool is ok
            await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
            await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)
            await ensure_state_root_hashes_are_in_sync(pool_handler, wallet_handler, trustee_did)