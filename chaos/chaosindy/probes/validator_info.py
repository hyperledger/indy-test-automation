import argparse
import json
import subprocess
import sys
from chaosindy.common import *
from chaosindy.execute.execute import FabricExecutor, ParallelFabricExecutor
from chaosindy.probes.validator_state import get_current_validator_list
from os.path import expanduser, join
from logzero import logger
from multiprocessing import Pool

from chaosindy.helpers import run
from chaosindy.ledger_interaction import get_validator_state

from typing import Union


def get_validator_info_from_node_serial(genesis_file: str,
    timeout: Union[str,int] = DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Get validator info for each node in the genesis file one at a time.

    See get_validator_info_from_node_parallel for a potentially (depends on how
    many cores your client has) more efficient option.

    The validator info is written to a file in the Chaos temp dir (see
    chaosindy.common.get_chaos_temp_dir). Each file is named in the following
    manner: '<node>-validator-info'.

    :param genesis_file: The relative or absolute path to the genesis
        transaction file.
        Required.
    :param timeout: How long the validator-info executable may execute before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT)
    :type timeout: str or int
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :return: bool
    """
    output_dir = get_chaos_temp_dir()
    logger.debug("genesis_file: %s ssh_config_file: %s", genesis_file,
                 ssh_config_file)
    # 1. Open genesis_file and load all aliases into an array
    aliases = []
    with open(expanduser(genesis_file), 'r') as genesisfile:
        for line in genesisfile:
            aliases.append(json.loads(line)['txn']['data']['data']['alias'])
    logger.debug(str(aliases))

    executor = FabricExecutor(ssh_config_file=expanduser(ssh_config_file))

    # Get get validator info from each alias
    count = len(aliases)
    logger.debug("Getting validator data from all %i nodes...", count)
    tried_to_query= 0
    are_queried = 0
    for alias in aliases:
        logger.debug("alias to query validator info from: %s", alias)
        result = executor.execute(alias, "validator-info -v --json",
                                  timeout=int(timeout), as_sudo=True)
        if result.return_code == 0:
            are_queried += 1
            # Write JSON output to temp directory output_dir, creating a unique
            # file name using the alias
            fname = "{}-validator-info".format(alias)
            with open(join(output_dir, fname), "w") as f:
                f.write(result.stdout)
        tried_to_query += 1

    logger.debug("are_queried: %s count: %i tried_to_query: %i len-aliases: %i",
                 are_queried, count, tried_to_query, len(aliases))
    if are_queried < int(count):
        return False

    return True


def get_validator_info_from_node_parallel(genesis_file: str,
    timeout: Union[str,int] = DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Get validator info for each node in the genesis file in parallel.

    The more cores your client has the faster validator info is collected from
    a pool.

    The validator info is written to a file in the Chaos temp dir (see
    chaosindy.common.get_chaos_temp_dir). Each file is named in the following
    manner: '<node>-validator-info'.

    :param genesis_file: The relative or absolute path to the genesis
        transaction file.
        Required.
    :param timeout: How long the validator-info executable may execute before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT)
    :type timeout: str or int
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :return: bool
    """
    output_dir = get_chaos_temp_dir()
    logger.debug("genesis_file: %s ssh_config_file: %s", genesis_file,
                 ssh_config_file)
    # 1. Open genesis_file and load all aliases into an array
    aliases = []
    with open(expanduser(genesis_file), 'r') as genesisfile:
        for line in genesisfile:
            aliases.append(json.loads(line)['txn']['data']['data']['alias'])
    logger.debug(str(aliases))

    expanded_ssh_config_file = expanduser(ssh_config_file)
    executor = ParallelFabricExecutor(ssh_config_file=expanded_ssh_config_file)

    # Get get validator info from each alias
    count = len(aliases)
    logger.debug("Getting validator data from all %i nodes...", count)
    tried_to_query = 0
    are_queried = 0
    logger.debug("alias to query validator info from: %s", str(aliases))
    result = executor.execute(aliases, "validator-info -v --json",
                              connect_timeout=int(timeout), as_sudo=True)

    for alias in aliases:
        if result[alias]['return_code'] == 0:
            are_queried += 1
            # Write JSON output to temp directory output_dir, creating a unique
            # file name using the alias
            fname = "{}-validator-info".format(alias)
            with open(join(output_dir, fname), "w") as f:
                f.write(result[alias]['stdout'])
        tried_to_query += 1

    logger.debug("are_queried: %s count: %i tried_to_query: %i len-aliases: %i",
                 are_queried, count, tried_to_query, len(aliases))
    if are_queried < int(count):
        return False

    return True


def get_validator_info_from_sdk(genesis_file: str, did: str,
    seed: str = DEFAULT_CHAOS_SEED,
    wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
    wallet_key: str = DEFAULT_CHAOS_WALLET_KEY, pool: str = DEFAULT_CHAOS_POOL,
    timeout: Union[str,int] = DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    *NYI*

    Get validator info using Indy SDK

    Perhaps enhancing chaosindy.ledger_intaraction.get_validator_state
    would be a good idea? It currently returns the latest pool ledger
    transaction for each node, but could be enhanced to include a superset of
    data for:
    1. What is currently included when calling get_validator_state
    2. Everything in the response from the 'validator-info' script or
       `ledger get-validator-info` indy-cli command

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param did: A steward or trustee DID. A did OR a seed is required, but not
        both. The did will be used if both are given. Needed to get validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_DID)
    :type did: str
    :param seed : A steward or trustee seed. A did OR a seed is required, but
        not both. The did will be used if both are given. Needed to get
        validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SEED)
    :type seed: str
    :param wallet_name: The name of the wallet to use when getting validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_NAME)
    :type wallet_name: str
    :param wallet_key: The key to use when opening the wallet designated by
        wallet_name.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_KEY)
    :type wallet_key: str
    :param pool: The pool to connect to when getting validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_POOL)
    :type pool: str
    :param timeout: How long indy-cli can take to perform the operation before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT)
    :type timeout: Union[str,int]
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :return: bool
    """
    #output_dir = get_chaos_temp_dir()
    #return True
    logger.error("NYI - get_validator_info_from_sdk is not yet implemented.")
    return False


def get_validator_info_from_cli(genesis_file: str, did: str,
    seed: str = DEFAULT_CHAOS_SEED,
    wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
    wallet_key: str = DEFAULT_CHAOS_WALLET_KEY, pool: str = DEFAULT_CHAOS_POOL,
    timeout: Union[str,int] = DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Get validator info using Indy CLI

     The following steps are required to configure the client node where
     indy-cli will be used to retrieve validator-info
     (i.e. common.ValidatorInfoSource.CLI is used in experiment):

     1. Install indy-cli
        `$ apt-get install indy-cli`
     2. Start indy-cli
        `$ indy-cli`
        `indy>`
     3. Create pool
        NOTE: Pool name will be a parameter for the experiments that need
              validator info
        `indy> pool create pool1 gen_txn_file=/home/ubuntu/indy-test-automation/chaos/pool_transactions_genesis`
     4. Create wallet
        NOTE: Wallet name and optional key will be parameters for the
              experiments that need validator info
        `indy> wallet create wallet1 key=key1`
     5. Open wallet created in the previous step
        `indy> wallet open wallet1 key=key1`
        `wallet(wallet1):indy>`
     6. Create did with a Trustee seed
        NOTE: did will be a parameter for the experiments that need validator
              info. validator info is only available to Trustees and Stewards
        `wallet(wallet1):indy> did new seed=000000000000000000000000Trustee1`
     7. Open pool created in previous step
        `wallet(wallet1):indy> pool connect pool1`
        `pool(pool1):wallet(wallet1):indy>`
     8. Verify the did created with the Trustee seed can retrieve validator info
        `pool(pool1):wallet(wallet1):indy> did use V4SGRU86Z58d6TV7PBUe6f`
        `pool(pool1):wallet(wallet1):did(V4S...e6f):indy>`
        `pool(pool1):wallet(wallet1):did(V4S...e6f):indy> ledger get-validator-info`

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param did: A steward or trustee DID. A did OR a seed is required, but not
        both. The did will be used if both are given. Needed to get validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_DID)
    :type did: str
    :param seed : A steward or trustee seed. A did OR a seed is required, but
        not both. The did will be used if both are given. Needed to get
        validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SEED)
    :type seed: str
    :param wallet_name: The name of the wallet to use when getting validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_NAME)
    :type wallet_name: str
    :param wallet_key: The key to use when opening the wallet designated by
        wallet_name.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_KEY)
    :type wallet_key: str
    :param pool: The pool to connect to when getting validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_POOL)
    :type pool: str
    :param timeout: How long indy-cli can take to perform the operation before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT)
    :type timeout: Union[str,int]
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :return: bool
    """

    '''
    To simplify the call to this function, perform a best-effort creation of
    pool, wallet, and did. Doing so eliminates the need to manually set them
    up prior to running experiments. Just pass the appropriate parameters to
    the experiment via the environment and they will be created the first time
    the experiment is run. All subsequent runs will generate a warning/error
    stating they already exist. Not a problem, because we are ignoring the
    error/warning. Note that indy-cli exists with a return code of 0 even if
    one of the commands in the file passed as a parameter fails.
    '''
    output_dir = get_chaos_temp_dir()

    # TODO: Do we want to get a list of aliases from the genesis file and make
    #       sure that indy-cli returns validator info for each node?

    # Pool creation
    indy_cli_command_batch = join(output_dir, "indy-cli-create-pool.in")
    with open(indy_cli_command_batch, "w") as f:
        f.write("pool create {} gen_txn_file={}\n".format(pool, genesis_file))
        f.write("exit")
    create_pool = subprocess.check_output(["indy-cli", indy_cli_command_batch],
                                          stderr=subprocess.STDOUT, shell=False)

    # Wallet creation
    indy_cli_command_batch = join(output_dir, "indy-cli-create-wallet.in")
    with open(indy_cli_command_batch, "w") as f:
        if wallet_key:
          f.write("wallet create {} key={}\n".format(wallet_name, wallet_key))
        else:
          f.write("wallet create {} key\n".format(wallet_name))
        f.write("exit")
    create_wallet = subprocess.check_output(
        ["indy-cli", indy_cli_command_batch], stderr=subprocess.STDOUT,
        shell=False)

    # DID creation
    if seed:
        indy_cli_command_batch = join(output_dir, "indy-cli-create-did.in")
        with open(indy_cli_command_batch, "w") as f:
            if wallet_key:
              f.write("wallet open {} key={}\n".format(wallet_name, wallet_key))
            else:
              f.write("wallet open {} key\n".format(wallet_name))
            f.write("did new seed={}\n".format(seed))
            f.write("exit")
        create_did = subprocess.check_output(
            ["indy-cli", indy_cli_command_batch], stderr=subprocess.STDOUT,
            shell=False)

    # Get validator information
    indy_cli_command_batch = join(output_dir, "indy-cli-get-validator-info.in")
    with open(indy_cli_command_batch, "w") as f:
        if wallet_key:
          f.write("wallet open {} key={}\n".format(wallet_name, wallet_key))
        else:
          f.write("wallet open {} key\n".format(wallet_name))
        f.write("did use {}\n".format(did))
        f.write("pool connect {}\n".format(pool))
        f.write("ledger get-validator-info timeout={}\n".format(timeout))
        f.write("pool disconnect\n")
        f.write("exit")
    # NOTE: Allow the subprocess to execute 5 seconds longer than the
    #       'ledger get-validator-info' CLI command
    all_validator_info = subprocess.check_output(
        ["indy-cli", indy_cli_command_batch], stderr=subprocess.STDOUT,
        timeout=int(timeout) + 5, shell=False)
    lines = all_validator_info.splitlines()
    # ledger get-validator-info returns a JSON string for each node to STDOUT
    # Each JSON string is preceeded by "Get validator info response for node..."
    # verbiage. Parse each line and write each nodes' JSON string to a
    # <node_name>-validator-info file
    #
    # NOTE: Can't use `for line in lines` combined with next(lines), because
    #       lines is an interable, but not an iterator.
    i = 0
    number_of_lines = len(lines)
    # Default to an empty dict
    json_output = "{}"
    append_line = False
    while i < number_of_lines:
        line = lines[i].decode()
        if not append_line and "Validator Info:" in line:
            # Clear the default
            json_output = ""
            append_line = True
        elif append_line and 'Transaction has been rejected: Client request is discarded since view change is in progress' in line:
            pass
            # Ignore this message
        elif append_line and (line == '' or line == 'exit'):
            # Append lines until the first blank line or the exit command is
            # encountered.
            break 
        elif append_line:
            json_output += line
        i += 1

    validator_info = json.loads(json_output)

    for k, v in validator_info.items():
        node_info_file = join(output_dir,
                              "{}-validator-info".format(k))
        if v != 'Timeout':
            with open(node_info_file, "w") as f:
                f.write(json.dumps(v['data']))
    return True


def get_validator_info_from_node(genesis_file: str,
    timeout: Union[str,int] = DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE,
    parallel: bool = True) -> bool:
    """
    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param timeout: How long the operation can execute before timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT)
    :type timeout: Union[str,int]
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :param parallel: Parallelize the retrieval of validator info?
    :type parallel: bool
        Optional (Default: True)
    :return: bool
    """
    if parallel:
        return get_validator_info_from_node_parallel(genesis_file,
            timeout=timeout, ssh_config_file=ssh_config_file)
    else:
        return get_validator_info_from_node_serial(genesis_file,
            timeout=timeout, ssh_config_file=ssh_config_file)


def get_validator_info(genesis_file: str, did: str = DEFAULT_CHAOS_DID,
    seed: str = DEFAULT_CHAOS_SEED,
    wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
    wallet_key: str = DEFAULT_CHAOS_WALLET_KEY, pool: str = DEFAULT_CHAOS_POOL,
    timeout: Union[str,int] = DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE,
    source: int = DEFAULT_CHAOS_VALIDATOR_INFO_SOURCE) -> bool:
    """
    Get validator info

    Validator info can be retrieved from any of the following:
      - A client that has indy-cli installed using `ledger get-validator-info`.
        This option provides more up-to-date information, but may take a long
        time to return results (100 sec default timeout when at least one node
        is down/unreachable). See ValidatorInfoSource.CLI in chaosindy/common.
      - A validator node using `validator-info -v --json`
        This option provides quicker results, but the data may be up to 60
        seconds stale/out-of-date.  See ValidatorInfoSource.NODE in
        chaosindy/common.
      - Possibly Indy SDK - TBD

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param did: A steward or trustee DID. A did OR a seed is required, but not
        both. The did will be used if both are given. Needed to get validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_DID)
    :type did: str
    :param seed : A steward or trustee seed. A did OR a seed is required, but
        not both. The did will be used if both are given. Needed to get
        validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SEED)
    :type seed: str
    :param wallet_name: The name of the wallet to use when getting validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_NAME)
    :type wallet_name: str
    :param wallet_key: The key to use when opening the wallet designated by
        wallet_name.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_KEY)
    :type wallet_key: str
    :param pool: The pool to connect to when getting validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_POOL)
    :type pool: str
    :param timeout: How long indy-cli can take to perform the operation before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT)
    :type timeout: Union[str,int]
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :param source: The source of validator info
        Optional. (Default: chaosindy.common.DEFAULT_VALIDATOR_INFO_SOURCE)
        Options: see chaosindy.common.ValidatorInfoSource
        - NODE (1) - validator-info script executed on each node
        - CLI (2) - Indy CLI
        - SDK (3) - Not Yet Implemented - Use Indy SDK
    :type source: int
    :return: bool
    """
    logger.debug("Getting validator info timeout: %d", int(timeout))
    if source == ValidatorInfoSource.NODE.value:
        logger.debug("Getting validator info using the validator-info script " \
                     "on each node.")
        return get_validator_info_from_node(genesis_file, timeout=timeout,
                                            ssh_config_file=ssh_config_file)
    elif source == ValidatorInfoSource.CLI.value:
        logger.debug("Getting validator info using indy-cli")
        return get_validator_info_from_cli(genesis_file, did=did, seed=seed,
                                           wallet_name=wallet_name,
                                           wallet_key=wallet_key, pool=pool,
                                           timeout=timeout,
                                           ssh_config_file=ssh_config_file)
    elif source == ValidatorInfoSource.SDK.value:
        logger.debug("Getting validator info using indy-sdk")
        return get_validator_info_from_sdk(genesis_file, did=did, seed=seed,
                                           wallet_name=wallet_name,
                                           wallet_key=wallet_key, pool=pool,
                                           timeout=timeout,
                                           ssh_config_file=ssh_config_file)
    else:
        logger.error("Unsupported validator info source: %s", source)
        return False


def detect_primary(genesis_file: str, did: str = DEFAULT_CHAOS_DID,
    seed: str = DEFAULT_CHAOS_SEED,
    wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
    wallet_key: str = DEFAULT_CHAOS_WALLET_KEY, pool: str = DEFAULT_CHAOS_POOL,
    timeout: Union[str,int] = DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Get the primary reported by each participating validator node.

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param did: A steward or trustee DID. A did OR a seed is required, but not
        both. The did will be used if both are given. Needed to get validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_DID)
    :type did: str
    :param seed : A steward or trustee seed. A did OR a seed is required, but
        not both. The did will be used if both are given. Needed to get
        validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SEED)
    :type seed: str
    :param wallet_name: The name of the wallet to use when getting validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_NAME)
    :type wallet_name: str
    :param wallet_key: The key to use when opening the wallet designated by
        wallet_name.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_KEY)
    :type wallet_key: str
    :param pool: The pool to connect to when getting validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_POOL)
    :type pool: str
    :param timeout: How long indy-cli can take to perform the operation before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT)
    :type timeout: Union[str,int]
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :return: bool
    """
    # 1. Get validator info from all nodes
    get_validator_info(genesis_file, did=did, seed=seed,
                       wallet_name=wallet_name,
                       wallet_key=wallet_key, pool=pool, timeout=timeout,
                       ssh_config_file=ssh_config_file)
    output_dir = get_chaos_temp_dir()

    logger.debug("genesis_file: %s ssh_config_file: %s", genesis_file,
                 ssh_config_file)
    # 2. Open genesis_file and load all aliases into an array
    aliases = []
    with open(expanduser(genesis_file), 'r') as genesisfile:
        for line in genesisfile:
            aliases.append(json.loads(line)['txn']['data']['data']['alias'])
    logger.debug(str(aliases))

    # Get the list of currently participating validator nodes
    current_validators = get_current_validator_list(genesis_file=genesis_file,
                                                    seed=seed,
                                                    pool_name=pool,
                                                    wallet_name=wallet_name,
                                                    wallet_key=wallet_key,
                                                    timeout=timeout)

    # 3. Get primary from each nodes validator-info
    primary_map = {}
    count_participating = 0
    count_not_participating = 0
    tried_to_query= 0
    for alias in aliases:
        # Only consider a node's declared primary as valid if it is a
        # participating validator node.
        if alias not in current_validators:
            logger.debug("%s is not currently participating as a validator" \
                         " node", alias)
            count_not_participating += 1
            continue
        count_participating += 1
        logger.debug("alias to query primary from validator info: %s", alias)
        validator_info = join(output_dir, "{}-validator-info".format(alias))
        logger.debug("Extract primary from %s", validator_info)

        try:
            with open(validator_info, 'r') as f:
                node_info = json.load(f)

            # For each node, Indy CLI returns json in a 'data' element
            if 'data' in node_info:
                data_node_info = node_info['data']['Node_info']
                replica_status = data_node_info['Replicas_status']
                primary = replica_status["{}:0".format(alias)]['Primary']
                primary = primary.split(":", 1)[0] if primary else None
                mode = data_node_info['Mode']
            else:
                # For each node, validator-info script does NOT return json in a
                # 'data' element
                replica_status = node_info['Node_info']['Replicas_status']
                primary = replica_status["{}:0".format(alias)]['Primary']
                primary = primary.split(":", 1)[0] if primary else None
                mode = node_info['Node_info']['Mode']
        except (FileNotFoundError, json.decoder.JSONDecodeError) as e:
            #logger.exception(e)
            logger.info("Failed to load validator info for alias " \
                        "{}".format(alias))
            logger.info("Setting primary to Unknown for alias {}".format(alias))
            primary = "Unknown"
            logger.info("Setting mode to Unknown for alias {}".format(alias))
            mode = "Unknown"
        except Exception as e:
            logger.error("Failed to load validator info for alias " \
                         "{}".format(alias))
            logger.exception(e)
            return False

        # Set the alias' primary
        alias_map = primary_map.get(alias, {})
        alias_map["primary"] = primary
        primary_map[alias] = alias_map
        if primary != 'Unknown':
            # Put the alias in the primary's is_primary_to list
            primary_alias_map = primary_map.get(primary, {})
            is_primary_to_list = primary_alias_map.get("is_primary_to", [])
            if alias not in is_primary_to_list:
                is_primary_to_list.append(alias)
            primary_alias_map['is_primary_to'] = is_primary_to_list
            primary_map[primary] = primary_alias_map

        logger.info("%s's primary is %s - mode: %s", alias, primary, mode)
        tried_to_query += 1
    logger.debug("Got primary node alias from %d participating validator" \
                 " nodes.", count_participating)

    # 4. Reconcile who is actually the primary. A primary is any node/alias with
    #    an is_primary_to list. However, the node/alias the majority of nodes
    #    reporting it as the primary is the actual primary.
    primary_map['node_count'] = count_participating
    nodes_with_is_primary_to_list = 0
    current_primary = None
    for alias in current_validators:
        alias_map = primary_map.get(alias, {})
        is_master_to_count = len(alias_map.get('is_primary_to', []))
        if is_master_to_count > 0:
            nodes_with_is_primary_to_list += 1
        if is_master_to_count > (count_participating / 2):
            alias_map['is_primary'] = True
            primary_map['current_primary'] = alias
    primary_map['reported_primaries'] = nodes_with_is_primary_to_list

    logger.debug("count_participating: %i count_not_participating: %i " \
                 "tried_to_query: %s len-aliases: %s",
                 count_participating, count_not_participating, tried_to_query,
                 len(aliases))
    if tried_to_query < int(count_participating):
        return False

    with open(join(output_dir, "primaries"), "w") as f:
        f.write(json.dumps(primary_map))

    return True


def detect_mode(genesis_file: str, did: str = DEFAULT_CHAOS_DID,
    seed: str = DEFAULT_CHAOS_SEED,
    wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
    wallet_key: str = DEFAULT_CHAOS_WALLET_KEY, pool: str = DEFAULT_CHAOS_POOL,
    timeout: Union[str,int] = DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Detect the mode of each node in the pool

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param did: A steward or trustee DID. A did OR a seed is required, but not
        both. The did will be used if both are given. Needed to get validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_DID)
    :type did: str
    :param seed : A steward or trustee seed. A did OR a seed is required, but
        not both. The did will be used if both are given. Needed to get
        validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SEED)
    :type seed: str
    :param wallet_name: The name of the wallet to use when getting validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_NAME)
    :type wallet_name: str
    :param wallet_key: The key to use when opening the wallet designated by
        wallet_name.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_KEY)
    :type wallet_key: str
    :param pool: The pool to connect to when getting validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_POOL)
    :type pool: str
    :param timeout: How long indy-cli can take to perform the operation before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT)
    :type timeout: Union[str,int]
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :return: bool
    """
    # 1. Get validator info from all nodes
    get_validator_info(genesis_file, did=did, seed=seed,
                       wallet_name=wallet_name,
                       wallet_key=wallet_key, pool=pool, timeout=timeout,
                       ssh_config_file=ssh_config_file)
    output_dir = get_chaos_temp_dir()

    logger.debug("genesis_file: %s ssh_config_file: %s", genesis_file,
                 ssh_config_file)
    # 2. Open genesis_file and load all aliases into an array
    aliases = []
    with open(expanduser(genesis_file), 'r') as genesisfile:
        for line in genesisfile:
            aliases.append(json.loads(line)['txn']['data']['data']['alias'])
    logger.debug(str(aliases))

    # 3. Get mode from each nodes validator-info
    mode_map = {}
    count = len(aliases)
    logger.debug("Getting mode from validator-info collected from all %i " \
                 "nodes...", count)
    tried_to_query= 0
    for alias in aliases:
        logger.debug("alias to query mode from validator info: %s", alias)
        validator_info = join(output_dir, "{}-validator-info".format(alias))
        logger.debug("Extract mode from %s", validator_info)

        try:
            with open(validator_info, 'r') as f:
                node_info = json.load(f)
            if 'data' in node_info:
                mode = node_info['data']['Node_info']['Mode']
            else:
                mode = node_info['Node_info']['Mode']
        except FileNotFoundError:
            logger.info("Failed to load validator info for alias " \
                        "{}".format(alias))
            logger.info("Setting mode to Unknown for alias {}".format(alias))
            mode = "Unknown"
        except Exception as e:
            logger.error("Failed to load validator info for alias " \
                         "{}".format(alias))
            logger.exception(e)
            return False

        logger.info("%s's mode is %s", alias, mode)
        # Set the alias' mode
        alias_map = mode_map.get(alias, {})
        alias_map["mode"] = mode
        mode_map[alias] = alias_map
        tried_to_query += 1

    logger.debug("count: %i tried_to_query: %s len-aliases: %s", count,
                 tried_to_query, len(aliases))
    if tried_to_query < int(count):
        return False

    with open(join(output_dir, "mode"), "w") as f:
        f.write(json.dumps(mode_map))

    return True


def nodes_in_mode(genesis_file: str, mode: str, count: Union[str,int],
    did: str = DEFAULT_CHAOS_DID, seed: str = DEFAULT_CHAOS_SEED,
    wallet_name: str = DEFAULT_CHAOS_WALLET_NAME,
    wallet_key: str = DEFAULT_CHAOS_WALLET_KEY, pool: str = DEFAULT_CHAOS_POOL,
    timeout: Union[str,int] = DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT,
    ssh_config_file: str = DEFAULT_CHAOS_SSH_CONFIG_FILE) -> bool:
    """
    Check if a given number of nodes are in a particular mode.

    :param genesis_file: The relative or absolute path to a genesis file.
        Required.
    :type genesis_file: str
    :param mode: The mode. Modes are defined in indy-plenum. See the Mode class
        in plenum/common/startable.py for details. Mode may include:
        starting
        discovering   - catching up on pool txn ledger
        discovered    - caught up with pool txn ledger
        syncing       - catching up on domain txn ledger
        synced        - caught up with domain txn ledger
        participating - caught up completely and chosen primary
        Required.
    :type mode: str
    :param count: The expected number of nodes in the given mode.
        Required.
    :type count: Union[str,int]
    :param did: A steward or trustee DID. A did OR a seed is required, but not
        both. The did will be used if both are given. Needed to get validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_DID)
    :type did: str
    :param seed : A steward or trustee seed. A did OR a seed is required, but
        not both. The did will be used if both are given. Needed to get
        validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SEED)
    :type seed: str
    :param wallet_name: The name of the wallet to use when getting validator
        info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_NAME)
    :type wallet_name: str
    :param wallet_key: The key to use when opening the wallet designated by
        wallet_name.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_WALLET_KEY)
    :type wallet_key: str
    :param pool: The pool to connect to when getting validator info.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_POOL)
    :type pool: str
    :param timeout: How long indy-cli can take to perform the operation before
        timing out.
        Optional.
        (Default: chaosindy.common.DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT)
    :type timeout: Union[str,int]
    :param ssh_config_file: The relative or absolute path to the SSH config
        file.
        Optional. (Default: chaosindy.common.DEFAULT_CHAOS_SSH_CONFIG_FILE)
    :type ssh_config_file: str
    :return: bool
    """
    # Must first get mode of each node using validator info.
    if not detect_mode(genesis_file, did=did, seed=seed,
                       wallet_name=wallet_name, wallet_key=wallet_key,
                       pool=pool, timeout=timeout,
                       ssh_config_file=ssh_config_file):
        return False

    output_dir = get_chaos_temp_dir()
    node_mode = {}
    with open("{}/mode".format(output_dir), 'r') as f:
       node_mode = json.load(f)

    ncount = 0
    for alias in node_mode.keys():
       nmode = node_mode[alias]['mode']
       if mode == nmode:
           ncount += 1

    if int(count) == ncount:
        return True
    else:
        return False
