import json
import re
import shutil
import tempfile
from enum import Enum
from logzero import logger
from os import makedirs
from os.path import expanduser
from psutil import Process, NoSuchProcess

from typing import Union, Dict, List

def get_chaos_temp_dir() -> str:
    """
    Create a temporary directory unique to each chaos experiment.
 
    The temporary directory will take the form <tempdir>/chaosindy.<pid>
    The <pid> will be the chaos processe's pid iff it exists. Otherwise, the
    subprocess's pid.

    :return: str
    """
    # Get current process info
    myp = Process()
    subprocess_pid = myp.pid
    chaos_pid = None
    # Walk all the way up the process tree
    while(1):
        #  Break when we find the 'chaos' process
        if myp.name() == 'chaos':
            logger.debug("Found 'chaos' process")
            chaos_pid = myp.pid
            break
        try:
            myp = Process(myp.ppid())
            logger.debug("myp.name=%s", myp.name())
        except NoSuchProcess as e:
            logger.info("Did not find chaos pid before traversing all the way" \
                        " to the top of the process tree! Defaulting to %s",
                        subprocess_pid)
            logger.exception(e)
            chaos_pid = subprocess_pid
            break

    logger.debug("subprocess pid: %s chaos pid: %s", subprocess_pid, chaos_pid)
    tempdir_path = "{}/chaosindy.{}".format(tempfile.gettempdir(), chaos_pid)
    tempdir = makedirs(tempdir_path, exist_ok=True)
    logger.debug("tempdir: %s", tempdir_path)
    return tempdir_path

def remove_chaos_temp_dir(cleanup: bool = True) -> bool:
    """
    Remove the chaos temp directory created by get_chaos_temp_dir

    :param cleanup: Perform the cleanup task?
    :type cleanup: bool
        Optional. (Default: True)
    :return: bool
    """
    temp_dir = get_chaos_temp_dir()
    if cleanup:
        logger.debug("Recursively deleting %s", temp_dir)
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error("Failed to recursively delete the contents of %s",
                         temp_dir)
            logger.exception(e)
            return False
    else:
        logger.info("Skip removal of %s.", temp_dir)
    return True

def get_info_by_node_name(genesis_file: str, node: str,
                          path: str = None) -> Union[Dict,None]:
    """
    Extract a node's information from the genesis transaction file

    :param genesis_file: The relative or absolute path to a genesis transaction
        file.
        Required.
    :type genesis_file: str
    :param node: The node name/alias
        Required.
    :type node: str
    :param path: A dot ('.') delimited path to traverse in the JSON doc.
        A value of None will resolve to txn.data.data
        Optional. (Default: None)
    :type node: str
    :return: Union[Dict,None]
    """
    # Open genesis_file and return a node's info based on a json path
    with open(expanduser(genesis_file), 'r') as genesisfile:
        for line in genesisfile:
            line_json = json.loads(line)
            alias = line_json['txn']['data']['data']['alias']
            if (alias == node):
                if not path:
                    return line_json['txn']['data']['data']
                else:
                    filters = path.split(".")
                    return_json = line_json
                    for f in filters:
                        return_json = return_json[f]
                    return return_json
    return None


def get_aliases(genesis_file: str) -> List[str]:
    """
    Return a complete list of aliases defined in a genesis file.

    The list of aliases will be in the same order they are defined (top down) in
    the genesis file.

    :param genesis_file: The relative or absolute path to a genesis transaction
        file.
        Required.
    :type genesis_file: str

    :return: List[str]
    """
    aliases = []
    # Open genesis_file and load all aliases into an array
    with open(expanduser(genesis_file), 'r') as genesisfile:
        for line in genesisfile:
            line_json = json.loads(line)
            alias = line_json['txn']['data']['data']['alias']
            aliases.append(alias)
    return aliases


# TODO: Consider adding a return_line_count, which would be the number of lines
#       to return after the offset (default would be 1).
def get_indy_cli_command_output(output: str, match: str,
    return_line_offset: int = 1, remove_ansi_escape_sequences: bool = True,
    multi: bool = False) -> Union[List[str],str]:
    """
    Get the output for a specific indy cli command from STDOUT captured calling
    indy-cli from python.

    :param output: STDOUT from a batch call to indy-cli from python.
        Required.
    :type output: str
    :param match: Find the first line in output that contains this string and
        return the next line from the output.
        Required.
    :type match: str
    :param return_line_offset: Find the first line in output that contains this
        string and return the next line from the output.
        Required.
    :type return_line_offset: int
    """
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')

    matches = []
    lines = iter(output.decode().split("\n"))
    for line in lines:
        if match in line:
            count = return_line_offset
            # Skip return_line_offset lines
            while(count > 0):
                line = lines.__next__()
                count -= 1
            # Return a single line just after return_line_offset lines have been
            # skipped
            if remove_ansi_escape_sequences:
                line = ansi_escape.sub('', line)
            matches.append(line)
            # Search for multiple matches?
            if multi:
                # Continue finding matches
                continue
            break
    if multi:
        return matches
    else:
        try:
            return matches[0]
        except IndexError:
            return None


class ValidatorInfoSource(Enum):
    """
    All possible sources (methods of retrieval) of validator info

    The SDK option is not yet implemented. It is stubbed out in hopes that the
    option will be available soon.
    """
    NODE = 1 # validator-info script executed on each node
    CLI = 2 # `ledger get-validator-info` executed via indy-cli
    SDK = 3 # Not Yet Implemented - Use Indy SDK to get validator info

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

# Actions and Probes may be written to select items/nodes on which to act/probe
# The following enum allows actions and probes to be written to operate on
# a set of items/nodes in a certain number of ways.
# Example: If there is an ordered set of nodes ['Node1', 'Node2', 'Node3'] and
#          two of them should be stopped (indy-node service stopped or node
#          port blocked), a FORWARD strategy would stop Node1, followed by
#          Node2.
#          A REVERSE strategy would stop Node3 followed by Node2. The RANDOM
#          strategy will pick a node at random, stop it, remove it from
#          consideration on the next selection and then repeat the process one
#          more time.
class SelectionStrategy(Enum):
    """
    All supported selection strategies.
    """
    FORWARD = 1
    REVERSE = 2
    RANDOM = 3

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

class StopStrategy(Enum):
    """
    All supported stop strategies.
    """
    #"stop" indy-node service
    SERVICE = 1
    # "stop/block" inbound messages from clients and other nodes
    PORT = 2
    # "stop" participating in consensus
    DEMOTE = 3
    # "stop/kill" indy-node service
    KILL = 4

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)

# Useful for validating boolean user input
true_list = [
   'true', '1', 't', 'y', 'yes'
]
false_list = [
   'false', '0', 'f', 'n', 'no'
]


# Chaos defaults
# Please keep defaults in lexically acending order by name unless they are based
# on other defaults. When based on other defaults, please define them after all
# defaults on which they depend. Dependent values must be defined first in bash.
DEFAULT_CHAOS_GET_VALIDATOR_INFO_TIMEOUT=20
DEFAULT_CHAOS_LEDGER_TRANSACTION_TIMEOUT=20
DEFAULT_CHAOS_LOAD_COMMAND="sudo python3 /home/ubuntu/indy-node/scripts/performance/perf_load/perf_processes.py -l 1 -c 2 -n 10 -b 200 -k nym -g /home/ubuntu/indy-test-automation/chaos/pool_transactions_genesis --load_time 10"
DEFAULT_CHAOS_LOAD_TIMEOUT=60
DEFAULT_CHAOS_NODE_SERVICES="VALIDATOR"
DEFAULT_CHAOS_PAUSE=60
DEFAULT_CHAOS_POOL="chaosindy"
DEFAULT_CHAOS_TRUSTEE_DICT = {
  1: {
      "seed": "000000000000000000000000Trustee1",
      "did": "V4SGRU86Z58d6TV7PBUe6f",
      "verkey": "~CoRER63DVYnWZtK8uAzNbx"
  },
  2: {
      "seed": "000000000000000000000000Trustee2",
      "did": "LnXR1rPnncTPZvRdmJKhJQ",
      "verkey": "~RTBtVN3iwcFhbWZzohFTMi"
  },
  3: {
      "seed": "000000000000000000000000Trustee3",
      "did": "PNQm3CwyXbN5e39Rw3dXYx",
      "verkey": "~AHtGeRXtGjVfXALtXP9WiX"
  },
  4: {
      "seed": "000000000000000000000000Trustee4",
      "did": "KMSWjAnqdwgLRc5yZBygcA",
      "verkey": "~SYaYSBf1ngDyM4VtKf7nxW"
  }
}
# TODO: Dynamically create the following trustee defaults, or refactor all uses
#       to use DEFAULT_CHAHOS_TRUSTEE_DICT?
DEFAULT_CHAOS_TRUSTEE_DID1=DEFAULT_CHAOS_TRUSTEE_DICT[1]["did"]
DEFAULT_CHAOS_DID=DEFAULT_CHAOS_TRUSTEE_DID1
DEFAULT_CHAOS_TRUSTEE_DID=DEFAULT_CHAOS_TRUSTEE_DID1
DEFAULT_CHAOS_TRUSTEE_DID2=DEFAULT_CHAOS_TRUSTEE_DICT[2]["did"]
DEFAULT_CHAOS_TRUSTEE_DID3=DEFAULT_CHAOS_TRUSTEE_DICT[3]["did"]
DEFAULT_CHAOS_TRUSTEE_DID4=DEFAULT_CHAOS_TRUSTEE_DICT[4]["did"]
DEFAULT_CHAOS_TRUSTEE_SEED=DEFAULT_CHAOS_TRUSTEE_DICT[1]["seed"]
DEFAULT_CHAOS_TRUSTEE_SEED1=DEFAULT_CHAOS_TRUSTEE_SEED
DEFAULT_CHAOS_TRUSTEE_SEED2=DEFAULT_CHAOS_TRUSTEE_DICT[2]["seed"]
DEFAULT_CHAOS_TRUSTEE_SEED3=DEFAULT_CHAOS_TRUSTEE_DICT[3]["seed"]
DEFAULT_CHAOS_TRUSTEE_SEED4=DEFAULT_CHAOS_TRUSTEE_DICT[4]["seed"]
DEFAULT_CHAOS_TRUSTEE_VERKEY=DEFAULT_CHAOS_TRUSTEE_DICT[1]["verkey"]
DEFAULT_CHAOS_TRUSTEE_VERKEY1=DEFAULT_CHAOS_TRUSTEE_VERKEY
DEFAULT_CHAOS_TRUSTEE_VERKEY2=DEFAULT_CHAOS_TRUSTEE_DICT[2]["verkey"]
DEFAULT_CHAOS_TRUSTEE_VERKEY3=DEFAULT_CHAOS_TRUSTEE_DICT[3]["verkey"]
DEFAULT_CHAOS_TRUSTEE_VERKEY4=DEFAULT_CHAOS_TRUSTEE_DICT[4]["verkey"]

DEFAULT_CHAOS_STEWARD_DICT = {
  1: {
      "seed": "000000000000000000000000Steward1"
  }
}
# TODO: Dynamically create the following steward defaults, or refactor all uses
#       to use DEFAULT_CHAHOS_STEWARD_DICT?
DEFAULT_CHAOS_STEWARD_SEED=DEFAULT_CHAOS_STEWARD_DICT[1]["seed"]
DEFAULT_CHAOS_SEED=DEFAULT_CHAOS_TRUSTEE_SEED

DEFAULT_CHAOS_SSH_CONFIG_FILE="~/.ssh/config"
DEFAULT_CHAOS_VALIDATOR_INFO_SOURCE=ValidatorInfoSource.CLI.value
DEFAULT_CHAOS_WALLET_NAME="chaosindy"
DEFAULT_CHAOS_MY_WALLET_NAME=DEFAULT_CHAOS_WALLET_NAME
DEFAULT_CHAOS_THEIR_WALLET_NAME="their_"+DEFAULT_CHAOS_WALLET_NAME
DEFAULT_CHAOS_WALLET_KEY="chaosindy"
DEFAULT_CHAOS_GENESIS_FILE="/home/ubuntu/indy-test-automation/chaos/pool_transactions_genesis"
