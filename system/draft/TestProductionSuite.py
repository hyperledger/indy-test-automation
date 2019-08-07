import pytest
import asyncio
from system.utils import *
from system.docker_setup import client, pool_builder, pool_starter,\
    DOCKER_BUILD_CTX_PATH, DOCKER_IMAGE_NAME, NODE_NAME_BASE, NETWORK_NAME, NETWORK_SUBNET

import logging
logger = logging.getLogger(__name__)

EXTRA_NODE_NAME_BASE = 'extra_{}'.format(NODE_NAME_BASE)
EXTRA_NODES_NUM = 5
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
        time.sleep(60)
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
                                   '{}{}'.format(SEED_PREFIX, i+nodes_num+1)],
                                  user='indy')
                    for i, node in enumerate(extra_containers)]
        start_res = [node.exec_run(['systemctl', 'start', 'indy-node'], user='root') for node in extra_containers]
        assert all([res.exit_code == 0 for res in init_res])
        assert all([res.exit_code == 0 for res in start_res])

        trustee_did, _ = get_default_trustee
        stewards = {}
        for i in range(5, EXTRA_NODES_NUM+5):
            steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(
                pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, 'Steward{}'.format(i), 'STEWARD'
            )
            assert res['op'] == 'REPLY'
            stewards['steward{}'.format(i)] = steward_did

        # TODO write and read txns and add nodes one by one at the same time

        # TODO write and read txns and demote/promote nodes one by one at the same time
