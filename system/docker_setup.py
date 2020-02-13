import os
import subprocess
import tarfile
from pathlib import Path
from subprocess import CalledProcessError
import docker

from .utils import (
    pool_helper, wallet_helper, default_trustee, ensure_pool_is_functional, ensure_all_nodes_online, NodeHost
)

import logging
logger = logging.getLogger(__name__)
# >>>>> set logging here <<<<<
logging.basicConfig(level=logging.NOTSET, format='%(asctime)s %(message)s')
# logging.basicConfig(level=logging.CRITICAL)

DOCKER_BUILD_CTX_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'docker', 'node'
)
DOCKER_IMAGE_NAME = os.environ.get('INDY_SYSTEM_TESTS_DOCKER_NAME', 'hyperledger/indy-test-automation:node')
NETWORK_NAME = os.environ.get('INDY_SYSTEM_TESTS_NETWORK', 'indy-test-automation-network')
# TODO limit subnet range to reduce risk of overlapping with system resources
NETWORK_SUBNET = os.environ.get('INDY_SYSTEM_TESTS_SUBNET', '10.0.0.0/24')
NODE_NAME_BASE = 'node'
NODES_NUM = int(os.environ.get('INDY_SYSTEM_NODES_NUM', 7))


client = docker.from_env()


def network_builder(network_subnet, network_name):
    client.networks.prune()

    try:
        client.networks.get(network_name)
        return network_name
    except docker.errors.NotFound:
        ipam_pool = docker.types.IPAMPool(subnet=network_subnet)
        ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
        return client.networks.create(name=network_name,
                                      ipam=ipam_config).name


def pool_builder(docker_build_ctx_path, node_image_name, node_name_base, network_name, nodes_num, start_from=0):
    try:
        image = client.images.get(node_image_name)
    except docker.errors.ImageNotFound:
        # build image from the Dockerfile
        output = []
        try:
            image, output = client.images.build(path=docker_build_ctx_path, tag=node_image_name)
        except Exception as exc:
            print("Failed to build docker image for Indy Node: {}".format(exc))
            raise
        finally:
            print(
                "Docker build logs ...\n:"
                "=====================\n"
            )
            for line in output:
                print(line)

    # enable systemd
    client.containers.run(image,
                          'setup',
                          remove=True,
                          privileged=True,
                          volumes={'/': {'bind': '/host', 'mode': 'rw'}})
    # run pool containers
    return [client.containers.run(image,
                                  name=node_name_base+str(i),
                                  detach=True,
                                  tty=True,
                                  network=network_name,
                                  volumes={'/sys/fs/cgroup': {'bind': '/sys/fs/cgroup', 'mode': 'ro'}},
                                  security_opt=['seccomp=unconfined'],
                                  tmpfs={'/run': '',
                                         '/run/lock': ''})
            for i in range(start_from + 1, start_from+nodes_num + 1)]


def pool_starter(node_containers):
    for node in node_containers:
        node.start()
    return node_containers


def pool_initializer(node_containers):
    indy_network_name = 'sandbox'
    ips = []
    for i in range(len(node_containers)):
        ips.append('.'.join(NETWORK_SUBNET.split('/')[0].split('.')[:3] + [str(i + 2)]))
    ips = ','.join(ips)
    init_res = [node.exec_run(['generate_indy_pool_transactions',
                               '--nodes', str(len(node_containers)),
                               '--clients', '1',
                               '--nodeNum', str(i+1),
                               '--ips', ips,
                               '--network', indy_network_name],
                              user='indy')
                for i, node in enumerate(node_containers)]
    start_res = [node.exec_run(['systemctl', 'start', 'indy-node'], user='root') for node in node_containers]
    assert all([res.exit_code == 0 for res in init_res])
    assert all([res.exit_code == 0 for res in start_res])
    return init_res, start_res


def pool_stop():
    print('\n---------------')
    containers = subprocess.check_output(
        ['docker', 'ps', '-a', '-q', '-f', "name={}*".format(NODE_NAME_BASE)]
    ).decode().strip().split()
    outputs = [subprocess.check_call(['docker', 'rm', container, '-f']) for container in containers]
    assert outputs is not None
    # Uncomment to destroy all images too
    # images = subprocess.check_output(['docker', 'images', '-q']).decode().strip().split()
    # try:
    #     outputs = [subprocess.check_call(['docker', 'rmi', image, '-f']) for image in images]
    #     assert outputs is not None
    # except CalledProcessError:
    #     pass


def main(nodes_num=None):
    nodes_num = NODES_NUM if nodes_num is None else nodes_num
    pool_initializer(
        pool_starter(
            pool_builder(
                DOCKER_BUILD_CTX_PATH,
                DOCKER_IMAGE_NAME,
                NODE_NAME_BASE,
                network_builder(NETWORK_SUBNET,
                                NETWORK_NAME),
                nodes_num)))


async def wait_until_pool_is_ready():
    wallet_handle, _, _ = await wallet_helper()
    trustee_did, _ = await default_trustee(wallet_handle)
    pool_handle, _ = await pool_helper()
    await ensure_all_nodes_online(pool_handle, wallet_handle, trustee_did)
    await ensure_pool_is_functional(pool_handle, wallet_handle, trustee_did)


def gather_logs(hosts, target_dir):
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    tmp_tar = target_dir / 'tmp.tar'

    try:
        for host in hosts:
            logs_path = host.generate_logs()
            bits, stat = client.containers.get(host.name).get_archive(logs_path)
            with open(str(tmp_tar), 'w+b') as f:
                for chunk in bits:
                    f.write(chunk)

            with tarfile.open(str(tmp_tar)) as tar:
                tar.extractall(str(target_dir))
    finally:
        if tmp_tar.exists():
            tmp_tar.unlink()


async def setup(nodes_num):
    pool_stop()

    main(nodes_num=nodes_num)
    await wait_until_pool_is_ready()
    logger.info('DOCKER SETUP HAS BEEN FINISHED!')


def teardown(nodes_num, nodes_logs_dir=None):
    try:
        if nodes_logs_dir:
            hosts = [NodeHost(node_id + 1) for node_id in range(nodes_num)]
            for host in hosts:
                host.stop_service()
            gather_logs(hosts, nodes_logs_dir)
    finally:
        pool_stop()
        logger.info('DOCKER TEARDOWN HAS BEEN FINISHED!\n')


def create_new_node(container_name, ip, alias, init_seed, sovrin_ver, node_ver, plenum_ver, plugin_ver):
    # create extra node
    new_node = pool_starter(
        pool_builder(
            DOCKER_BUILD_CTX_PATH, DOCKER_IMAGE_NAME, container_name, NETWORK_NAME, 1
        )
    )[0]

    GENESIS_PATH = '/var/lib/indy/sandbox/'

    # put both genesis files
    print(new_node.exec_run(['mkdir', GENESIS_PATH], user='indy'))

    for _, prefix in enumerate(['pool', 'domain']):
        bits, stat = client.containers.get('node1'). \
            get_archive('{}{}_transactions_genesis'.format(GENESIS_PATH, prefix))
        assert new_node.put_archive(GENESIS_PATH, bits)

    new_ip = ip
    PORT_1 = '9701'
    PORT_2 = '9702'

    # initialize
    res = new_node.exec_run(
        ['init_indy_node', alias, new_ip, PORT_1, new_ip, PORT_2, init_seed],
        user='indy'
    )
    assert res.exit_code == 0

    # upgrade it to the target version of pool upgrade command
    res = new_node.exec_run(
        ['apt', 'update'],
        user='root'
    )
    assert res.exit_code == 0

    res = new_node.exec_run(
        ['apt', 'install',
         '{}={}'.format('sovrin', sovrin_ver),
         '{}={}'.format('indy-node', node_ver),
         '{}={}'.format('indy-plenum', plenum_ver),
         '{}={}'.format('sovtoken', plugin_ver),
         '{}={}'.format('sovtokenfees', plugin_ver),
         '-y', '--allow-change-held-packages'],
        user='root'
    )
    assert res.exit_code == 0

    return new_node


if __name__ == '__main__':
    main()
