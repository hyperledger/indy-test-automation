import docker


def test_ubuntu18():
    client = docker.from_env()
    name = 'ubuntu1804client'
    try:
        client.containers.get(name).remove(force=True)
    except docker.errors.NotFound:
        pass
    image, output = client.images.build(
        path='.', dockerfile='_ubuntu18.dockerfile', tag=name
    )
    print('\nBuild logs:')
    for line in output:
        print(line)
    container = client.containers.run(image, name=name, detach=True, tty=True)
    container.start()
    res = str(container.exec_run('dpkg -l'))
    checks = ['libindy', 'indy-cli', 'libnullpay', 'libvcx']
    assert all([check in res for check in checks])
    print(res)
