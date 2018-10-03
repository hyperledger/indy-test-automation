import os
import json
import subprocess
from chaosindy.common import *
from logzero import logger
from os.path import expanduser, join
from typing import Union, List, Dict


def delete_wallet(wallet_name: str, wallet_key: str = None) -> bool:
    """
    Delete a wallet with the given name; using the key if given.

    :param wallet_name: The name of the wallet to delete
        Required.
    :type wallet_name: str
    :param wallet_key: The key to use when deleting the wallet
        Optional. (Default: None)
    :type wallet_key: str
    :return: bool
    """
    output_dir = get_chaos_temp_dir()

    # Delete the wallet
    indy_cli_command_batch = join(output_dir, "indy-cli-delete-wallet.in")
    with open(indy_cli_command_batch, "w") as f:
        if wallet_key:
          f.write("wallet delete {} key={}\n".format(wallet_name, wallet_key))
        else:
          f.write("wallet delete {} key\n".format(wallet_name))
        f.write("exit")
    try:
        indy_cli_delete_wallet = subprocess.check_output(
            ["indy-cli", indy_cli_command_batch], stderr=subprocess.STDOUT,
            shell=False)
    except subprocess.CalledProcessError as e:
        indy_cli_command_output = join(output_dir, "indy-cli-delete-wallet.out")
        # Write available exception data to an output file in JSON format.
        # May be useable in an experiment.
        with open(indy_cli_command_output, "w") as f:
            output = {
                'returncode': f.returncode,
                'cmd': f.cmd,
                'output': f.output
            }
            f.write(json.dumps(output))
        return False

    return True

def create_wallet(wallet_name: str, wallet_key: str = None) -> bool:
    """
    Create a wallet with the given name; using the key if given.

    :param wallet_name: The name of the wallet to create
        Required.
    :type wallet_name: str
    :param wallet_key: The key to use when creating the wallet
        Optional. (Default: None)
    :type wallet_key: str
    :return: bool
    """
    output_dir = get_chaos_temp_dir()

    # Delete the wallet
    indy_cli_command_batch = join(output_dir, "indy-cli-create-wallet.in")
    with open(indy_cli_command_batch, "w") as f:
        if wallet_key:
          f.write("wallet create {} key={}\n".format(wallet_name, wallet_key))
        else:
          f.write("wallet create {} key\n".format(wallet_name))
        f.write("exit")
    try:
        indy_cli_create_wallet = subprocess.check_output(
            ["indy-cli", indy_cli_command_batch], stderr=subprocess.STDOUT,
            shell=False)
    except subprocess.CalledProcessError as e:
        indy_cli_command_output = join(output_dir, "indy-cli-create-wallet.out")
        # Write available exception data to an output file in JSON format.
        # May be useable in an experiment.
        with open(indy_cli_command_output, "w") as f:
            output = {
                'returncode': f.returncode,
                'cmd': f.cmd,
                'output': f.output
            }
            f.write(json.dumps(output))
        return False

    return True
