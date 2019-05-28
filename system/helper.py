import time
import subprocess
from subprocess import CalledProcessError
from async_generator import yield_

import system.docker_setup


async def docker_setup_and_teardown():

    system.docker_setup.pool_stop()

    system.docker_setup.main()
    time.sleep(30)
    print('\nDOCKER SETUP HAS BEEN FINISHED!\n')
    await yield_()

    system.docker_setup.pool_stop()
    print('\nDOCKER TEARDOWN HAS BEEN FINISHED!\n')
