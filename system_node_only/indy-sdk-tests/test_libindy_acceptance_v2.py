import docker
import testinfra


def test_libindy():
    client = docker.from_env()
    client_name = 'libindy_acceptance_client'
    pool_name = 'libindy_acceptance_pool'
    sdk_ver = '1.14.3-rc-127'

    try:
        client.containers.get(client_name).remove(force=True)
    except docker.errors.NotFound:
        pass

    try:
        client.containers.get(pool_name).remove(force=True)
    except docker.errors.NotFound:
        pass

    # pool setup
    pool_image, output = client.images.build(
        path='.', dockerfile='_libindy_acceptance_pool.dockerfile', tag=pool_name
    )  # use `buildargs` (dict): A dictionary of build arguments
    print('\nBuild logs:')
    for line in output:
        print(line)
    # use `environment` (dict or list): Environment variables to set inside the container
    pool_container = client.containers.run(pool_image, name=pool_name, network='host', detach=True, tty=True)
    pool_container.start()

    # client setup
    client_image, output = client.images.build(
        path='.', dockerfile='_libindy_acceptance_client.dockerfile', tag=client_name
    )  # use `buildargs` (dict): A dictionary of build arguments
    print('\nBuild logs:')
    for line in output:
        print(line)
    # use `environment` (dict or list): Environment variables to set inside the container
    client_container = client.containers.run(client_image, name=client_name, network='host', detach=True, tty=True)
    client_container.start()

    pom_update = client_container.exec_run(
        ['sed',
         '-i',
         '112c\\\t\t\t<version>{}</version>'.format(sdk_ver),
         '/indy-sdk/samples/java/pom.xml']
    )
    assert pom_update.exit_code == 0

    setup_update = client_container.exec_run(
        ['sed',
         '-i',
         '11c\\    install_requires=[\'python3-indy=={}\']'.format(sdk_ver),
         '/indy-sdk/samples/python/setup.py']
    )
    assert setup_update.exit_code == 0

    host = testinfra.get_host("docker://{}".format(client_name))

    java_result = host.run(
        'cd /indy-sdk/samples/java '
        '&& TEST_POOL_IP=127.0.0.1 mvn clean compile exec:java -Dexec.mainClass="Main"'
    )
    java_checks = [
        'Anoncreds sample -> completed', 'Anoncreds Revocation sample -> completed', 'Ledger sample -> completed',
        'Crypto sample -> completed', 'BUILD SUCCESS'
    ]
    assert all([check in java_result.stdout for check in java_checks])

    python_result = host.run(
        'cd /indy-sdk/samples/python '
        '&& python3.5 -m pip install --user -e . '
        '&& TEST_POOL_IP=127.0.0.1 python3.5 src/main.py'
    )
    python_checks = [
        'Getting started -> done', 'Anoncreds Revocation sample -> completed', 'Anoncreds sample -> completed',
        'Crypto sample -> completed', 'Ledger sample -> completed', 'Transaction Author Agreement sample -> completed'
    ]
    assert all([check in python_result.stderr for check in python_checks])
