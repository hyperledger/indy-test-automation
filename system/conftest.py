import pytest
import json
import asyncio
import os
from datetime import datetime
from async_generator import async_generator, yield_

from indy import pool, payment, did, ledger

from .utils import (
    pool_helper, wallet_helper, default_trustee,
    check_no_failures, NodeHost, payment_initializer,
    send_nym
)
from .docker_setup import setup, teardown

ATOMS = 100000
PAYMENT_METHOD = 'sov'
_failed_nodes = {}


def pytest_configure(config):
    config.addinivalue_line(
        "markers", "nodes_num(int): mark test to run specific number of nodes in pool, default: 7"
    )


def pytest_addoption(parser):
    parser.addoption(
        "--payments", action='store_true', default=None,
        help="run payment oriented tests as well"
    )
    parser.addoption(
        "--gatherlogs", action='store_true', default=None,
        help="gather node logs for failed tests"
    )
    parser.addoption(
        "--logsdir", action='store', default='_build/logs',
        help="directory name to store logs"
    )


# based on https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    if rep.when == 'call' and rep.failed:
        _failed_nodes[item.nodeid] = item
        # TODO ensure that parent is always points to module
        _failed_nodes[item.parent.nodeid] = item.parent


# TODO seems not the best name for that functionality
@pytest.fixture(scope='session', autouse=True)
def event_loop():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(pool.set_protocol_version(2))
    yield loop
    loop.close()


@pytest.fixture(scope='session', autouse=True)
def session_name():
    return "run.{}".format(datetime.now().strftime("%Y-%m-%dT%H%M%S"))


@pytest.fixture()
@async_generator
async def pool_handler(event_loop):
    pool_handle, _ = await pool_helper()
    await yield_(pool_handle)


@pytest.fixture()
@async_generator
async def aws_pool_handler(event_loop):
    pool_handle, _ = await pool_helper(path_to_genesis='../aws_genesis_test')
    await yield_(pool_handle)


@pytest.fixture()
@async_generator
async def wallet_handler(event_loop):
    wallet_handle, _, _ = await wallet_helper()
    await yield_(wallet_handle)


@pytest.fixture()
@async_generator
async def get_default_trustee(wallet_handler):
    trustee_did, trustee_vk = await default_trustee(wallet_handler)
    await yield_((trustee_did, trustee_vk))


# TODO different payment plugins (libsovtoken, libnullpay, ...)
@pytest.fixture(scope="module")
def payment_init_module(request):
    if True or request.config.getoption("payments"):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(payment_initializer('libsovtoken.so', 'sovtoken_init'))


@pytest.fixture()
def payment_init(request, payment_init_module):
    # it will skips any test that depends on payment plugins
    # if pytest is run without '--payments' option
    # (more details: https://docs.pytest.org/en/latest/reference.html#_pytest.config.Config.getoption)
    request.config.getoption("payments", skip=False)


@pytest.fixture()
@async_generator
async def initial_token_minting(payment_init, pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    address = await payment.create_payment_address(
        wallet_handler, PAYMENT_METHOD, json.dumps({"seed": str('0000000000000000000000000Wallet0')})
    )
    trustee_did_second, trustee_vk_second = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    trustee_did_third, trustee_vk_third = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_second, trustee_vk_second, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_third, trustee_vk_third, None, 'TRUSTEE')
    req, _ = await payment.build_mint_req(
        wallet_handler, trustee_did, json.dumps([{'recipient': address, 'amount': 1000 * ATOMS}]), None
    )
    req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_second, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_third, req)
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    await yield_(address)


@pytest.fixture()
@async_generator
async def initial_fees_setting(payment_init, pool_handler, wallet_handler, get_default_trustee):
    trustee_did, _ = get_default_trustee
    trustee_did_second, trustee_vk_second = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    trustee_did_third, trustee_vk_third = await did.create_and_store_my_did(wallet_handler, json.dumps({}))
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_second, trustee_vk_second, None, 'TRUSTEE')
    await send_nym(pool_handler, wallet_handler, trustee_did, trustee_did_third, trustee_vk_third, None, 'TRUSTEE')
    fees = {
        'trustee_0': 0 * ATOMS,
        'steward_0': 0 * ATOMS,
        'trust_anchor_0': 0 * ATOMS,
        'network_monitor_0': 0 * ATOMS,
        'add_identity_owner_50': 50 * ATOMS,
        'edit_identity_owner_0': 0 * ATOMS,
        'add_schema_250': 250 * ATOMS,
        'add_cred_def_125': 125 * ATOMS,
        'add_rrd_100': 100 * ATOMS,
        'add_rre_0_5': int(0.5 * ATOMS)
        }
    req = await payment.build_set_txn_fees_req(
        wallet_handler, trustee_did, PAYMENT_METHOD, json.dumps(fees)
    )
    req = await ledger.multi_sign_request(wallet_handler, trustee_did, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_second, req)
    req = await ledger.multi_sign_request(wallet_handler, trustee_did_third, req)
    res = json.loads(await ledger.submit_request(pool_handler, req))
    assert res['op'] == 'REPLY'
    await yield_(fees)


@pytest.fixture(scope='function')
async def nodes_num(request):
    marker = request.node.get_closest_marker('nodes_num')
    return marker.args[0] if marker else 7


@pytest.fixture(scope='module')
async def nodes_num_module(request):
    return 7


# TODO options instead:
#   - use template
#   - use docker connection
@pytest.fixture(scope='function', autouse=True)
async def ssh_config():
    NODES_NUM = 25  # get rid of nodes_num consuming and always create ssh config for 25 nodes
    if os.environ.get('IN_DOCKER_ENV') != 'yes':
        return

    config_entry = (
        "Host node{node_id}\n"
        "    HostName 10.0.0.{node_ip_part}\n"
        "    User root\n"
        "    IdentityFile ~/.ssh/test_key\n"
        "    StrictHostKeyChecking no"
    )
    config = '\n'.join([
        config_entry.format(node_id=(i + 1), node_ip_part=(i + 2))
        for i in range(NODES_NUM)
    ])
    with open(os.path.expanduser('~/.ssh/config'), 'w') as f:
        f.write(config)


@pytest.fixture(scope='module')
def _docker_teardown(session_name):
    def wrapped(nodes_num, request):
        logs_dir = None
        if (request.node.nodeid in _failed_nodes) and request.config.getoption("gatherlogs"):
            logs_dir = os.path.join(request.config.getoption("logsdir"), session_name, request.node.nodeid)

        # fix for prod case
        if request.node.name == 'test_case_complex_pool_operations':
            nodes_num = 11
        # -----------------

        teardown(nodes_num, logs_dir)
    return wrapped


@pytest.fixture(scope='module')
@async_generator
async def docker_setup_and_teardown_module(nodes_num_module, request, _docker_teardown):
    await setup(nodes_num_module)
    await yield_()
    _docker_teardown(nodes_num_module, request)


@pytest.fixture(scope='function')
@async_generator
async def docker_setup_and_teardown_function(nodes_num, request, _docker_teardown):
    await setup(nodes_num)
    await yield_()
    _docker_teardown(nodes_num, request)


@pytest.fixture(scope='function')
@async_generator
async def docker_setup_and_teardown(docker_setup_and_teardown_function):
    await yield_()


@pytest.fixture
def check_no_failures_fixture(request, docker_setup_and_teardown, nodes_num):
    marker = request.node.get_closest_marker('check_no_failures_interval')
    check_interval = 20 if marker is None else marker.args[0]

    loop = asyncio.get_event_loop()
    hosts = [NodeHost(node_id + 1) for node_id in range(nodes_num)]

    stop = False

    def check():
        try:
            if not stop:
                check_no_failures(hosts)
        except AssertionError as ex:
            pytest.fail()
        else:
            if not stop:
                loop.call_later(check_interval, check)

    loop.call_later(check_interval, check)
    yield
    stop = True
