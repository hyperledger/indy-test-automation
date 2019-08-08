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
EXTRA_DESTS = [
    '4Tn3wZMNCvhSTXPcLinQDnHyj56DTLQtL61ki4jo2Loc',
    '6G9QhQa3HWjRKeRmEvEkLbWWf2t7cw6KLtafzi494G4G',
    'BeLdccGjNcCDpVNCbxCFb4CfZWGxLCSM4CfGFFoZ443V',
    'CJqRrPMjPec5wvHDoggvxYUk13fXDbya3Aopc4TiFkNr',
    'GYUibLwguJX5YcEYmy1xE45j6cbdnSjyJm9bKPiM163Z',
    '67NLWsr8dFJrL6cDWcZkDce4hoSSGPBesk2PzqvGqL1R',
    '4UjwEpgGVqpyovAxFRVP5mn2S4m6UHq2CftzeE73YrNq'
]
EXTRA_BLSKEYS = [
    '2RdajPq6rCidK5gQbMzSJo1NfBMYiS3e44GxjTqZUk3RhBdtF28qEABHRo4MgHS2hwekoLWRTza9XiGEMRCompeujWpX85MPt87WdbTMysXZfb7J1ZXUEMrtE5aZahfx6p2YdhZdrArFvTmFWdojaD2V5SuvuaQL4G92anZ1yteay3R',
    'zi65fRHZjK2R8wdJfDzeWVgcf9imXUsMSEY64LQ4HyhDMsSn3Br1vhnwXHE7NyGjxVnwx4FGPqxpzY8HrQ2PnrL9tu4uD34rjgPEnFXnsGAp8aF68R4CcfsmUXfuU51hogE7dZCvaF9GPou86EWrTKpW5ow3ifq16Swpn5nKMXHTKj',
    'oApJaiaS9tKPGxb7svdDWvRSKYKFE8mFJVQyEQsRRqUMDeFQwLqRgrtxNfCtYrunCjzFmaMjFDnSy8a5n1ZCpp3TGH8oXJ8s4i7H9Yiy5hz2uPc3ManS9HiTvQE3TcBfxkuXswmR3Esy9Qi7LUjCuWGoi7fkwB3wATcLMJ5AuYr8mB',
    '4ZaPVUjKWct8pQ3NJxC3GDA9LZqk8bPLaLmncBCPk33NbQnF1FyAvkkfj2Kmh1BbrJN6eXH6suGTvPFkrpSyLcmyp9CHJoiibdXi6mKEftNBbekepf7vzGvAmqgybzcPy1dqrykWyKVVQPQwmXXtGqNB2eafuwx8TECWakJHcJTA6AC',
    '2ngTBQLDh78H3o7u7FpZMUgcpjuQ4brqh5v2bEj3Xs84GGVpnAbihmdQcsba8WNwrvBK6ScPa8kLLfKikZBmsVtFpPxPjD9rdT8YsGrSnYCkJARr2DKzyupKDqVncVY7ahg8Q1cDeqqgbdZwGnaAA1gSKNWjH2LRNaXF2dYh2Gjkrdo'
]
EXTRA_BLSKEY_POPS = [
    'RbGAR89T5bg6Bg66Xg1fy5NjVarmvr8Q7XAmEPCA6arPvcfcDwLiEftD2cCVoEnrRSPLhgf3Cn9n81gdgMCbSBEhKuWW3njXkPFE1jvP67bU1d2jb6gw5BxyxsF9qg1Hvz6pr181u7s1WZBmGXinLoKaFhb6jptHghHvtqEuTgoqXM',
    'QocoFNfnfbFxLobP9DeUgH2gDPc3FjB44JpfnHo9RosCDubw6AJeRj84avhBKpFqxuVQMpyXwPZ5uPVGfdadsjywrLsfABoeBw1JAvDckzAjaKDvhu1K7LX8zpzaQewWmt8VcWovyiaDJDDSdJQycvfQxzWk5G93iP26zwAriq7wYK',
    'QqURauAZ5zhjW9yVMtGxTLLDfnAxAhavzmuSUmMosmVZLSkcYEcywHHaxi7axkpRJmsg4kmeZk1tzC4zUQrRDLc7FgcfCuTN15ub3JkynAh29x76nr7KxeHWLwMZVMyzMc5fiUfxWk2RbChitZmbbzqTVQSpjodh8TJgZX4b5p9ap7',
    'RSZ6uTEGrXkzRMFztZRQkFJCH13BJFZC7G5DqF8K7J5YoHYsdaTzSQqGDjKaUMcuRuiUsTUta8udcF31JFJpszNzqdxTUjy5fAVFd2h2U2xW6SiucjGKGP88uNnx4eWv28P4HpaCd7A3cPxfnWpnpCtywRguqFa4TRurYZK5eTW7XM',
    'Rbe2kBioQxNvxcbn46oe31AjDBdMMBjSgZfsN3jhfyK4r7512h815HKugx7ttr6z3AKCQmXJMz3EWPMKZMDe8Km1od1p2oiURNPjhT56jjKhkhGUzm91ndgUaM7MctGmdGJJC2R65uorvhNa7mckm76r3rvLW2ZGQd4f4YfavYsFDq'
]


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

        # TODO write and read txns and demote/promote nodes one by one at the same time
