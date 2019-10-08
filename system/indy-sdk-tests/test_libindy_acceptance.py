import os
import subprocess
import testinfra


def test_libindy():
    indy_plenum_ver = '1.10.0~rc1'
    indy_node_ver = '1.10.0~rc1'
    pyzmq_ver = '18.1.0'
    indy_sdk_deb_path = 'https://repo.sovrin.org/sdk/lib/apt/xenial/rc/'
    indy_sdk_deb_ver = 'libindy_1.12.0~96_amd64.deb'
    indy_sdk_ver = '1.12.0-rc-96'
    os.chdir('/home/indy/indy-sdk')
    subprocess.check_call(['git', 'stash'])
    subprocess.check_call(['git', 'fetch'])
    subprocess.check_call(['git', 'checkout', 'origin/rc'])
    subprocess.check_call(['sed', '-i', '22c\\ARG indy_stream=rc', './ci/indy-pool.dockerfile'])
    subprocess.check_call(['sed', '-i', '27c\\ARG indy_plenum_ver={}'.format(indy_plenum_ver),
                           './ci/indy-pool.dockerfile'])
    subprocess.check_call(['sed', '-i', '28c\\ARG indy_node_ver={}'.format(indy_node_ver),
                           './ci/indy-pool.dockerfile'])
    subprocess.check_call(['sed', '-i', '31c\\ARG python3_pyzmq_ver={}'.format(pyzmq_ver),
                           './ci/indy-pool.dockerfile'])
    # set version of `indy` dependency in `pom.xml` to libindy version
    subprocess.check_call(['sed', '-i', '112c\\\t\t\t<version>{}</version>'.format(indy_sdk_ver),
                           './samples/java/pom.xml'])
    # set version of `python3-indy` dependency in `setup.py` to libindy version
    subprocess.check_call(['sed', '-i', '11c\\    install_requires=[\'python3-indy=={}\']'.format(indy_sdk_ver),
                           './samples/python/setup.py'])
    subprocess.check_call(['docker', 'build', '-f', 'ci/indy-pool.dockerfile', '-t', 'indy_pool', '.'])
    subprocess.check_call(['docker', 'run', '-itd', '-p', '9701-9709:9701-9709', 'indy_pool'])
    pool_id = subprocess.check_output(['docker', 'build', '--build-arg', 'indy_sdk_deb={}'.
                                       format(indy_sdk_deb_path+indy_sdk_deb_ver), '-f',
                                       'ci/acceptance/ubuntu_acceptance.dockerfile', '.'])[-13:-1].decode().strip()
    print(pool_id)
    client_id = subprocess.check_output(['docker', 'run', '-itd', '-v',
                                         '/home/indy/indy-sdk/samples:/home/indy/samples', '--network=host', pool_id])\
        .decode().strip()
    print(client_id)
    host = testinfra.get_host("docker://{}".format(client_id))

    # test java
    java_res = host.run(
        'cd /home/indy/samples/java && TEST_POOL_IP=127.0.0.1 mvn clean compile exec:java -Dexec.mainClass="Main"'
    )
    print(java_res)
    java_checks = [
        'Anoncreds sample -> completed', 'Anoncreds Revocation sample -> completed', 'Ledger sample -> completed',
        'Crypto sample -> completed', 'BUILD SUCCESS'
    ]
    for check in java_checks:
        assert java_res.stdout.find(check) is not -1
    host.run('rm -rf /home/indy/.indy_client')

    # test python
    host.run('cd /home/indy/samples/python && python3.5 -m pip install --user -e .')
    python_res = host.run('cd /home/indy/samples/python && TEST_POOL_IP=127.0.0.1 python3.5 src/main.py')
    print(python_res)
    python_checks = [
        'Getting started -> done', 'Anoncreds Revocation sample -> completed', 'Anoncreds sample -> completed',
        'Crypto sample -> completed', 'Ledger sample -> completed', 'Transaction Author Agreement sample -> completed'
    ]
    for check in python_checks:
        assert python_res.stderr.find(check) is not -1
    host.run('rm -rf /home/indy/.indy_client')

    # test node.js
    # TODO
