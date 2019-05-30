import os
import subprocess
from subprocess import CalledProcessError
import docker


DOCKER_BUILD_CTX_PATH = os.path.join(
    os.path.abspath(os.path.dirname(__file__)), 'docker', 'node'
)
DOCKER_IMAGE_NAME = os.environ.get('INDY_SYSTEM_TESTS_DOCKER_NAME', 'hyperledger/indy-test-automation:node')
NETWORK_NAME = os.environ.get('INDY_SYSTEM_TESTS_NETWORK', 'indy-test-automation-network')
# TODO limit subnet range to reduce risk of overlapping with system resources
NETWORK_SUBNET = os.environ.get('INDY_SYSTEM_TESTS_SUBNET', '10.0.0.0/24')
NODE_NAME_BASE = 'node'
NODES_NUM = 7


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


def pool_builder(docker_build_ctx_path, node_image_name, node_name_base, network_name, nodes_num):
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
            for i in range(1, nodes_num+1)]


def pool_starter(node_containers):
    for node in node_containers:
        node.start()
    return node_containers


def pool_initializer(node_containers):
    ips = []
    for i in range(len(node_containers)):
        ips.append('.'.join(NETWORK_SUBNET.split('/')[0].split('.')[:3] + [str(i + 2)]))
    ips = ','.join(ips)
    init_res = [node.exec_run(['generate_indy_pool_transactions',
                               '--nodes', str(len(node_containers)),
                               '--clients', '1',
                               '--nodeNum', str(i+1),
                               '--ips', ips],
                              user='indy')
                for i, node in enumerate(node_containers)]
    start_res = [node.exec_run(['systemctl', 'start', 'indy-node'], user='root') for node in node_containers]
    assert all([res.exit_code == 0 for res in init_res])
    assert all([res.exit_code == 0 for res in start_res])
    return init_res, start_res

def pool_stop():
    containers = subprocess.check_output([
        'docker', 'ps', '-a', '-q', '-f', "name={}*".format(NODE_NAME_BASE)
    ]).decode().strip().split()
    outputs = [subprocess.check_call(['docker', 'rm', container, '-f']) for container in containers]
    assert outputs is not None
    # Uncomment to destroy all images too
    # images = subprocess.check_output(['docker', 'images', '-q']).decode().strip().split()
    # try:
    #     outputs = [subprocess.check_call(['docker', 'rmi', image, '-f']) for image in images]
    #     assert outputs is not None
    # except CalledProcessError:
    #     pass


def main():
    print(pool_initializer(
            pool_starter(
                pool_builder(
                    DOCKER_BUILD_CTX_PATH,
                    DOCKER_IMAGE_NAME,
                    NODE_NAME_BASE,
                    network_builder(NETWORK_SUBNET,
                                    NETWORK_NAME),
                    NODES_NUM))))


if __name__ == '__main__':
    main()
