import os
import json
import random
import subprocess
import time
import multiprocessing as mp
from chaosindy.common import *
from chaosindy.execute.execute import (FabricExecutor, ParallelFabricExecutor,
    NonDaemonicChaosPool)
from chaosindy.actions.node import clean_by_node_name
from logzero import logger
from os.path import expanduser, join
from time import sleep
from typing import Union, List, Dict

def _clean_pool_worker(arg):
    node, ledger_data_dir, clean_ledger, clean_logs, clean_iptables, ssh_config_file = arg
    # Call clean_pool recursively, but with a list of one node and parallelize
    # set to False
    return clean_pool([node],
                      ledger_data_dir=ledger_data_dir,
                      clean_ledger=clean_ledger,
                      clean_logs=clean_logs,
                      clean_iptables=clean_iptables,
                      ssh_config_file=ssh_config_file,
                      parallelize=False)

def clean_pool(aliases: List[str],
    ledger_data_dir: str = '/var/lib/indy/sandbox',
    clean_ledger: str = 'Y',
    clean_logs: str = 'Y',
    clean_iptables: str = 'Y',
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE,
    parallelize: bool = True) -> bool:
    """
    Remove the ledger data, ledger log files, and/or iptables INPUT rules.

    :param aliases: The list of aliases for the nodes in the pool
        Required.
    :type aliases: List[str]
    :param ledger_data_dir: The location of the ledger's 'data' directory
        Optional. (Default: "/var/lib/indy/sandbox")
    :type ledger_data_dir: str
    :param clean_ledger: Delete the ledger's data directory? This parameter is
        case insensitive.
        Valid true options include: 'y', 'yes', '1', 't', 'true'
        Valid false options include: 'n', 'no', '0', 'f', 'false'
        Optional. (Default: "Yes")
    :type clean_ledger: str
    :param clean_logs: Delete the ledger's logs? This parameter is case
        insensitive.
        Valid true options include: 'y', 'yes', '1', 't', 'true'
        Valid false options include: 'n', 'no', '0', 'f', 'false'
        Optional. (Default: "Yes")
    :type clean_logs: str
    :param clean_iptables: Remove all INPUT iptables rules? This parameter is
        case insensitive.
        Valid true options include: 'y', 'yes', '1', 't', 'true'
        Valid false options include: 'n', 'no', '0', 'f', 'false'
        Optional. (Default: "Yes")
    :type clean_iptables: str
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :param parallelize: Clean as many nodes in parallel as possible?
        Optional. (Default: True)
    :type parallelize: bool
    :return: bool
    """

    if not parallelize:
        # Call clean_node_by_name for each node in the pool
        for alias in aliases:
            if not clean_by_node_name(alias, ledger_data_dir=ledger_data_dir,
                                      clean_ledger=clean_ledger,
                                      clean_logs=clean_logs,
                                      clean_iptables=clean_iptables,
                                      ssh_config_file=ssh_config_file):
                return False
    else:
        arg_tuples = [(alias, ledger_data_dir, clean_ledger, clean_logs,
            clean_iptables, ssh_config_file) for alias in aliases]
        list_of_results = [False]
        with NonDaemonicChaosPool(processes=4) as pool:
            list_of_results = pool.map(_clean_pool_worker, arg_tuples)
        if False in list_of_results:
            return False

    return True

def clean_pool_by_genesis_file(
    genesis_file: str = '/home/ubuntu/indy-test-automation/chaos/pool_transactions_genesis',
    ledger_data_dir: str = '/var/lib/indy/sandbox',
    clean_ledger: str = 'Y',
    clean_logs: str = 'Y',
    clean_iptables: str = 'Y',
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE,
    parallelize: bool = True) -> bool:
    """
    Remove the ledger data, ledger log files, and/or iptables INPUT rules.

    :param genesis_file: The genesis transaction file for the pool
        Optional. (Default: "/home/ubuntu/indy-test-automation/chaos/pool_transactions_genesis")
    :type genesis_file: str
    :param ledger_data_dir: The location of the ledger's 'data' directory
        Optional. (Default: "/var/lib/indy/sandbox")
    :type ledger_data_dir: str
    :param clean_ledger: Delete the ledger's data directory? This parameter is
        case insensitive.
        Valid true options include: 'y', 'yes', '1', 't', 'true'
        Valid false options include: 'n', 'no', '0', 'f', 'false'
        Optional. (Default: "Yes")
    :type clean_ledger: str
    :param clean_logs: Delete the ledger's logs? This parameter is case
        insensitive.
        Valid true options include: 'y', 'yes', '1', 't', 'true'
        Valid false options include: 'n', 'no', '0', 'f', 'false'
        Optional. (Default: "Yes")
    :type clean_logs: str
    :param clean_iptables: Remove all INPUT iptables rules? This parameter is
        case insensitive.
        Valid true options include: 'y', 'yes', '1', 't', 'true'
        Valid false options include: 'n', 'no', '0', 'f', 'false'
        Optional. (Default: "Yes")
    :type clean_iptables: str
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :param parallelize: Clean as many nodes in parallel as possible?
        Optional. (Default: True)
    :type parallelize: bool
    :return: bool
    """

    # Get each node in the pool
    aliases = get_aliases(genesis_file)

    return clean_pool(aliases, ledger_data_dir, clean_ledger, clean_logs,
                      clean_iptables, ssh_config_file, parallelize)
