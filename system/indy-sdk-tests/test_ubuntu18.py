import docker


def test_ubuntu18():
    client = docker.from_env()
    name = 'ubuntu1804client'
    try:
        client.containers.get(name).remove(force=True)
    except docker.errors.NotFound:
        pass
    image, output = client.images.build(path='.', tag='ubuntu1804')
    print('\nBuild logs:')
    for line in output:
        print(line)
    container = client.containers.run(image, name=name, detach=True, tty=True)
    container.start()
    res = container.exec_run('dpkg -l')
    checks = ['libindy', 'indy-cli', 'libnullpay', 'libvcx']
    assert all([str(res).find(check) is not -1 for check in checks])
    print(res)
