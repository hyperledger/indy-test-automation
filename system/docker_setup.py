import docker


client = docker.from_env()
DOCKERFILE_PATH = '.'
NETWORK_SUBNET = '10.0.0.0/8'
NETWORK_NAME = 'custom'
NODE_NAME_BASE = 'node'
NODES_NUM = 7


def network_builder(network_subnet, network_name):
    client.networks.prune()
    ipam_pool = docker.types.IPAMPool(subnet=network_subnet)
    ipam_config = docker.types.IPAMConfig(pool_configs=[ipam_pool])
    return client.networks.create(name=network_name,
                                  ipam=ipam_config).name


def pool_builder(dockerfile_path, node_name_base, network_name, nodes_num):
    # build image from Dockerfile
    image, _ = client.images.build(path=dockerfile_path)
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
    ips = [NETWORK_SUBNET[:-3]+str(i+2) for i in range(len(node_containers))]
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


if __name__ == '__main__':
    print(pool_initializer(
        pool_starter(
            pool_builder(
                DOCKERFILE_PATH,
                NODE_NAME_BASE,
                network_builder(NETWORK_SUBNET,
                                NETWORK_NAME),
                NODES_NUM))))


def main():
    print(pool_initializer(
            pool_starter(
                pool_builder(
                    DOCKERFILE_PATH,
                    NODE_NAME_BASE,
                    network_builder(NETWORK_SUBNET,
                                    NETWORK_NAME),
                    NODES_NUM))))
