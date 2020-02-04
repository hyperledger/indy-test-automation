import pytest
from system.utils import *
from system.docker_setup import client, pool_builder, pool_starter,\
    DOCKER_BUILD_CTX_PATH, DOCKER_IMAGE_NAME, NODE_NAME_BASE, NETWORK_NAME, NETWORK_SUBNET


# EXTRA_NODE_NAME_BASE = 'extra_{}'.format(NODE_NAME_BASE)
EXTRA_NODE_NAME_BASE = NODE_NAME_BASE
EXTRA_NODES_NUM = 7
PORT_1 = '9701'
PORT_2 = '9702'
ALIAS_PREFIX = 'Node'
SEED_PREFIX = '000000000000000000000000000node'
GENESIS_PATH = '/var/lib/indy/sandbox/'
NYMS_COUNT = 5


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestProductionSuite:

    @pytest.mark.nodes_num(4)
    @pytest.mark.asyncio
    async def test_case_complex_pool_operations(
            self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    ):
        # create extra nodes
        extra_containers = pool_starter(
            pool_builder(
                DOCKER_BUILD_CTX_PATH, DOCKER_IMAGE_NAME, EXTRA_NODE_NAME_BASE, NETWORK_NAME, EXTRA_NODES_NUM,
                start_from=4
            )
        )

        # put both genesis files into extra nodes
        print([c.exec_run(['mkdir', GENESIS_PATH], user='indy') for c in extra_containers])

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
        await asyncio.sleep(15)  # FIXME intermittent failure with locked db files

        trustee_did, _ = get_default_trustee
        stewards = {}

        for i in range(1, nodes_num+1):
            steward_did, steward_vk = await did.create_and_store_my_did(
                wallet_handler, json.dumps({'seed': '000000000000000000000000Steward{}'.format(i)})
            )
            stewards['steward{}'.format(i)] = steward_did

        for i in range(nodes_num+1, EXTRA_NODES_NUM+nodes_num+1):
            steward_did, steward_vk = await did.create_and_store_my_did(wallet_handler, '{}')
            res = await send_nym(
                pool_handler, wallet_handler, trustee_did, steward_did, steward_vk, 'Steward{}'.format(i), 'STEWARD'
            )
            assert res['op'] == 'REPLY'
            stewards['steward{}'.format(i)] = steward_did

        print(stewards)

        # add 5th node
        res = await send_node(
            pool_handler, wallet_handler, ['VALIDATOR'], trustee_did, EXTRA_DESTS[0],
            ALIAS_PREFIX+str(nodes_num+1), EXTRA_BLSKEYS[0], EXTRA_BLSKEY_POPS[0],
            ips[0], int(PORT_2), ips[0], int(PORT_1)
        )
        assert res['op'] == 'REJECT'  # negative case - trustee adds node

        primary1, _, _ = await get_primary(pool_handler, wallet_handler, trustee_did)
        res5 = await send_node(
            pool_handler, wallet_handler, ['VALIDATOR'], stewards['steward5'], EXTRA_DESTS[0],
            ALIAS_PREFIX+str(nodes_num+1), EXTRA_BLSKEYS[0], EXTRA_BLSKEY_POPS[0],
            ips[0], int(PORT_2), ips[0], int(PORT_1)
        )
        assert res5['op'] == 'REPLY'
        primary2 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary1)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # add 6th node
        res = await send_node(
            pool_handler, wallet_handler, ['VALIDATOR'], stewards['steward5'], EXTRA_DESTS[1],
            ALIAS_PREFIX+str(nodes_num+2), EXTRA_BLSKEYS[1], EXTRA_BLSKEY_POPS[1],
            ips[1], int(PORT_2), ips[1], int(PORT_1)
        )
        assert res['op'] == 'REJECT'  # negative case - steward that already has node adds another one

        res6 = await send_node(
            pool_handler, wallet_handler, ['VALIDATOR'], stewards['steward6'], EXTRA_DESTS[1],
            ALIAS_PREFIX+str(nodes_num+2), EXTRA_BLSKEYS[1], EXTRA_BLSKEY_POPS[1],
            ips[1], int(PORT_2), ips[1], int(PORT_1)
        )
        assert res6['op'] == 'REPLY'
        primary3 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary2)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # add 7th node
        res7 = await send_node(
            pool_handler, wallet_handler, ['VALIDATOR'], stewards['steward7'], EXTRA_DESTS[2],
            ALIAS_PREFIX+str(nodes_num+3), EXTRA_BLSKEYS[2], EXTRA_BLSKEY_POPS[2],
            ips[2], int(PORT_2), ips[2], int(PORT_1)
        )
        assert res7['op'] == 'REPLY'
        await pool.refresh_pool_ledger(pool_handler)
        primary4 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary3)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # add 8th node
        res8 = await send_node(
            pool_handler, wallet_handler, ['VALIDATOR'], stewards['steward8'], EXTRA_DESTS[3],
            ALIAS_PREFIX+str(nodes_num+4), EXTRA_BLSKEYS[3], EXTRA_BLSKEY_POPS[3],
            ips[3], int(PORT_2), ips[3], int(PORT_1)
        )
        assert res8['op'] == 'REPLY'
        primary5 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary4)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # add 9th node
        res9 = await send_node(
            pool_handler, wallet_handler, ['VALIDATOR'], stewards['steward9'], EXTRA_DESTS[4],
            ALIAS_PREFIX+str(nodes_num+5), EXTRA_BLSKEYS[4], EXTRA_BLSKEY_POPS[4],
            ips[4], int(PORT_2), ips[4], int(PORT_1)
        )
        assert res9['op'] == 'REPLY'
        primary6 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary5)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # add 10th node
        res10 = await send_node(
            pool_handler, wallet_handler, ['VALIDATOR'], stewards['steward10'], EXTRA_DESTS[5],
            ALIAS_PREFIX+str(nodes_num+6), EXTRA_BLSKEYS[5], EXTRA_BLSKEY_POPS[5],
            ips[5], int(PORT_2), ips[5], int(PORT_1)
        )
        assert res10['op'] == 'REPLY'
        await pool.refresh_pool_ledger(pool_handler)
        primary7 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary6)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # add 11th node
        res11 = await send_node(
            pool_handler, wallet_handler, ['VALIDATOR'], stewards['steward11'], EXTRA_DESTS[6],
            ALIAS_PREFIX+str(nodes_num+7), EXTRA_BLSKEYS[6], EXTRA_BLSKEY_POPS[6],
            ips[6], int(PORT_2), ips[6], int(PORT_1)
        )
        assert res11['op'] == 'REPLY'
        primary8 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary7)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        pool_info = get_pool_info(primary8)
        print(pool_info)

        # demote initial 1st node by trustee
        await eventually(demote_node, pool_handler, wallet_handler, trustee_did, 'Node1', pool_info['Node1'])
        await pool.refresh_pool_ledger(pool_handler)
        primary9 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary8)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # demote initial 2nd node by trustee
        await eventually(
            demote_node, pool_handler, wallet_handler, trustee_did, 'Node2', pool_info['Node2']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary10 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary9)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # demote initial 3rd node by trustee
        await eventually(
            demote_node, pool_handler, wallet_handler, trustee_did, 'Node3', pool_info['Node3']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary11 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary10)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # demote initial 4th node by trustee
        await eventually(
            demote_node, pool_handler, wallet_handler, trustee_did, 'Node4', pool_info['Node4']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary12 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary11)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # demote 5th node by trustee
        await eventually(
            demote_node, pool_handler, wallet_handler, trustee_did, 'Node5', pool_info['Node5']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary13 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary12)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # demote 6th node by trustee
        await eventually(
            demote_node, pool_handler, wallet_handler, trustee_did, 'Node6', pool_info['Node6']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary14 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary13)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # demote 11th node by owner
        with pytest.raises(AssertionError):  # negative case - steward demotes node that he doesn't own
            await demote_node(pool_handler, wallet_handler, stewards['steward5'], 'Node11', pool_info['Node11'])

        await eventually(
            demote_node, pool_handler, wallet_handler, stewards['steward11'], 'Node11', pool_info['Node11']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary15 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary14)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # promote 11th node by trustee
        with pytest.raises(AssertionError):  # negative case - steward promotes node that he doesn't own
            await promote_node(pool_handler, wallet_handler, stewards['steward6'], 'Node11', pool_info['Node11'])

        await eventually(
            promote_node, pool_handler, wallet_handler, trustee_did, 'Node11', pool_info['Node11']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary16 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary15)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # promote 6th node by owner
        await eventually(
            promote_node, pool_handler, wallet_handler, stewards['steward6'], 'Node6', pool_info['Node6']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary17 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary16)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # promote 5th node by owner
        await eventually(
            promote_node, pool_handler, wallet_handler, stewards['steward5'], 'Node5', pool_info['Node5']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary18 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary17)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # promote initial 4th node by owner
        await eventually(
            promote_node, pool_handler, wallet_handler, stewards['steward4'], 'Node4', pool_info['Node4']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary19 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary18)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # promote initial 3rd node by owner
        await eventually(
            promote_node, pool_handler, wallet_handler, stewards['steward3'], 'Node3', pool_info['Node3']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary20 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary19)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # promote initial 2nd node by owner
        await eventually(
            promote_node, pool_handler, wallet_handler, stewards['steward2'], 'Node2', pool_info['Node2']
        )
        await pool.refresh_pool_ledger(pool_handler)
        primary21 = await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary20)
        await ensure_all_nodes_online(pool_handler, wallet_handler, trustee_did)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)
        await ensure_ledgers_are_in_sync(pool_handler, wallet_handler, trustee_did)

        # promote initial 1st node by owner
        await eventually(
            promote_node, pool_handler, wallet_handler, stewards['steward1'], 'Node1', pool_info['Node1']
        )
        await pool.refresh_pool_ledger(pool_handler)
        await ensure_primary_changed(pool_handler, wallet_handler, trustee_did, primary21)
        await ensure_pool_performs_write_read(pool_handler, wallet_handler, trustee_did, nyms_count=NYMS_COUNT)

        await ensure_pool_is_okay(pool_handler, wallet_handler, trustee_did)

    # # TODO implement upgrade chain test case
    # @pytest.mark.asyncio
    # async def test_case_upgrade_chain(
    #         self, pool_handler, wallet_handler, get_default_trustee, nodes_num
    # ):
    #     pass
