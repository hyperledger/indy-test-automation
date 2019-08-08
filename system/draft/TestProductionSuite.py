import pytest
import asyncio
from system.utils import *
from system.docker_setup import client, pool_builder, pool_starter,\
    DOCKER_BUILD_CTX_PATH, DOCKER_IMAGE_NAME, NODE_NAME_BASE, NETWORK_NAME, NETWORK_SUBNET

import logging
logging.basicConfig(
    level=0, format='%(asctime)s %(message)s'
)

EXTRA_NODE_NAME_BASE = 'extra_{}'.format(NODE_NAME_BASE)
EXTRA_NODES_NUM = 7
PORT_1 = '9701'
PORT_2 = '9702'
ALIAS_PREFIX = 'Node'
SEED_PREFIX = '000000000000000000000000000node'
GENESIS_PATH = '/var/lib/indy/sandbox/'


class TestProductionSuite:

    @pytest.mark.nodes_num(4)
    @pytest.mark.asyncio
    async def test_case_complex_pool_creation(
            self, docker_setup_and_teardown, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        # create extra nodes
        extra_containers = pool_starter(
            pool_builder(
                DOCKER_BUILD_CTX_PATH, DOCKER_IMAGE_NAME, EXTRA_NODE_NAME_BASE, NETWORK_NAME, EXTRA_NODES_NUM
            )
        )
        # put both genesis files into extra nodes
        assert all([c.exec_run(['mkdir', GENESIS_PATH], user='indy').exit_code == 0 for c in extra_containers])
        for node in extra_containers:
            for _, prefix in enumerate(['pool', 'domain']):
                bits, stat = client.containers.get('node1'). \
                    get_archive('{}{}_transactions_genesis'.format(GENESIS_PATH, prefix))
                assert node.put_archive(GENESIS_PATH, bits)
        # gather their ips
        ips = []
        for i in range(len(extra_containers)):
            ips.append('.'.join(NETWORK_SUBNET.split('/')[0].split('.')[:3] + [str(i + 6)]))
        # initialize them and run services
        init_res = [node.exec_run(['init_indy_node',
                                   '{}{}'.format(ALIAS_PREFIX, i+nodes_num+1),
                                   ips[i],
                                   PORT_1,
                                   ips[i],
                                   PORT_2,
                                   '{}{}'.format(SEED_PREFIX, i+nodes_num+1)
                                   if (i+nodes_num+1) < 10
                                   else '{}{}'.format(SEED_PREFIX[1:], i+nodes_num+1)],
                                  user='indy')
                    for i, node in enumerate(extra_containers)]
        start_res = [node.exec_run(['systemctl', 'start', 'indy-node'], user='root') for node in extra_containers]
        assert all([res.exit_code == 0 for res in init_res])
        assert all([res.exit_code == 0 for res in start_res])
        time.sleep(15)  # FIXME intermittent failure with locked db files

        trustee_did, _ = get_default_trustee
        stewards = {}
        for i in range(5, EXTRA_NODES_NUM+5):
            steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(
                pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, 'Steward{}'.format(i), 'STEWARD'
            )
            assert res['op'] == 'REPLY'
            stewards['steward{}'.format(i)] = steward_did

        # add 5th node
        res5 = await send_node(
            pool_handler, wallet_handler, ALIAS_PREFIX+str(nodes_num+1), EXTRA_BLSKEYS[0], EXTRA_BLSKEY_POPS[0],
            ips[0], int(PORT_2), ips[0], int(PORT_1), ['VALIDATOR'], stewards['steward5'], EXTRA_DESTS[0]
        )
        assert res5['op'] == 'REPLY'
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=5, timeout=30)
        await ensure_pool_is_in_sync(nodes_num=5)

        # add 6th node
        res6 = await send_node(
            pool_handler, wallet_handler, ALIAS_PREFIX+str(nodes_num+2), EXTRA_BLSKEYS[1], EXTRA_BLSKEY_POPS[1],
            ips[1], int(PORT_2), ips[1], int(PORT_1), ['VALIDATOR'], stewards['steward6'], EXTRA_DESTS[1]
        )
        assert res6['op'] == 'REPLY'
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=10, timeout=30)
        await ensure_pool_is_in_sync(nodes_num=6)

        # add 7th node - f will be changed - VC
        primary_first, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        res7 = await send_node(
            pool_handler, wallet_handler, ALIAS_PREFIX+str(nodes_num+3), EXTRA_BLSKEYS[2], EXTRA_BLSKEY_POPS[2],
            ips[2], int(PORT_2), ips[2], int(PORT_1), ['VALIDATOR'], stewards['steward7'], EXTRA_DESTS[2]
        )
        assert res7['op'] == 'REPLY'
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_first)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=15, timeout=30)
        await ensure_pool_is_in_sync(nodes_num=7)

        # add 8th node
        res8 = await send_node(
            pool_handler, wallet_handler, ALIAS_PREFIX+str(nodes_num+4), EXTRA_BLSKEYS[3], EXTRA_BLSKEY_POPS[3],
            ips[3], int(PORT_2), ips[3], int(PORT_1), ['VALIDATOR'], stewards['steward8'], EXTRA_DESTS[3]
        )
        assert res8['op'] == 'REPLY'
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=20, timeout=30)
        await ensure_pool_is_in_sync(nodes_num=8)

        # add 9th node
        res9 = await send_node(
            pool_handler, wallet_handler, ALIAS_PREFIX+str(nodes_num+5), EXTRA_BLSKEYS[4], EXTRA_BLSKEY_POPS[4],
            ips[4], int(PORT_2), ips[4], int(PORT_1), ['VALIDATOR'], stewards['steward9'], EXTRA_DESTS[4]
        )
        assert res9['op'] == 'REPLY'
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=25, timeout=30)
        await ensure_pool_is_in_sync(nodes_num=9)

        # add 10th node - f will be changed - VC
        primary_second, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        res10 = await send_node(
            pool_handler, wallet_handler, ALIAS_PREFIX+str(nodes_num+6), EXTRA_BLSKEYS[5], EXTRA_BLSKEY_POPS[5],
            ips[5], int(PORT_2), ips[5], int(PORT_1), ['VALIDATOR'], stewards['steward10'], EXTRA_DESTS[5]
        )
        assert res10['op'] == 'REPLY'
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary_second)
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=30, timeout=30)
        await ensure_pool_is_in_sync(nodes_num=10)

        # add 11th node
        res11 = await send_node(
            pool_handler, wallet_handler, ALIAS_PREFIX+str(nodes_num+7), EXTRA_BLSKEYS[6], EXTRA_BLSKEY_POPS[6],
            ips[6], int(PORT_2), ips[6], int(PORT_1), ['VALIDATOR'], stewards['steward11'], EXTRA_DESTS[6]
        )
        assert res11['op'] == 'REPLY'
        await ensure_pool_is_functional(pool_handler, wallet_handler, trustee_did, nyms_count=35, timeout=30)
        await ensure_pool_is_in_sync(nodes_num=11)

        # TODO write and read txns and demote/promote nodes one by one at the same time
