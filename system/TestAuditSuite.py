import pytest
from system.utils import *


@pytest.mark.usefixtures('docker_setup_and_teardown')
class TestAuditSuite:

    @pytest.mark.asyncio
    async def test_case_1(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        hosts = [testinfra.get_host('ssh://node{}'.format(i)) for i in range(1, 8)]
        for i in range(15):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        output = hosts[5].check_output('systemctl restart indy-node')
        print(output)
        for i in range(30):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        time.sleep(30)
        check_ledger_sync()
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        output = testinfra.get_host('ssh://node{}'.format(primary1)).check_output('systemctl stop indy-node')
        print(output)
        time.sleep(60)
        for i in range(15):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        output = hosts[5].check_output('systemctl restart indy-node')
        print(output)
        for i in range(30):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        output = testinfra.get_host('ssh://node{}'.format(primary1)).check_output('systemctl start indy-node')
        print(output)
        primary2, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        output = testinfra.get_host('ssh://node{}'.format(primary2)).check_output('systemctl stop indy-node')
        print(output)
        time.sleep(60)
        output = hosts[5].check_output('systemctl stop indy-node')
        print(output)
        output = testinfra.get_host('ssh://node{}'.format(primary2)).check_output('systemctl start indy-node')
        print(output)
        for i in range(15):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        output = hosts[5].check_output('systemctl start indy-node')
        print(output)
        for i in range(30):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        time.sleep(30)
        check_ledger_sync()

    @pytest.mark.asyncio
    async def test_case_2(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        hosts = [testinfra.get_host('ssh://node{}'.format(i)) for i in range(1, 8)]
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        output = testinfra.get_host('ssh://node{}'.format(primary1)).check_output('systemctl stop indy-node')
        print(output)
        time.sleep(60)
        for i in range(15):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        output = testinfra.get_host('ssh://node{}'.format(primary1)).check_output('systemctl start indy-node')
        print(output)
        output = hosts[1].check_output('systemctl restart indy-node')
        print(output)
        for i in range(30):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        time.sleep(30)
        check_ledger_sync()

    @pytest.mark.asyncio
    async def test_case_3(self, pool_handler, wallet_handler, get_default_trustee):
        trustee_did, _ = get_default_trustee
        hosts = [testinfra.get_host('ssh://node{}'.format(i)) for i in range(1, 8)]
        primary1, alias, target_did = await get_primary(pool_handler, wallet_handler, trustee_did)
        output = testinfra.get_host('ssh://node{}'.format(primary1)).check_output('systemctl stop indy-node')
        print(output)
        time.sleep(60)
        for i in range(15):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        output = testinfra.get_host('ssh://node{}'.format(primary1)).check_output('systemctl start indy-node')
        print(output)
        outputs = [host.check_output('systemctl restart indy-node') for host in hosts]
        print(outputs)
        time.sleep(30)
        for i in range(30):
            await nym_helper(pool_handler, wallet_handler, trustee_did, random_did_and_json()[0], None, None, None)
        time.sleep(30)
        check_ledger_sync()
