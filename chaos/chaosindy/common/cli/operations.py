"""
Common operations for CLI strategy
"""
from chaosindy.common import get_indy_cli_command_output
from chaosindy.common.cli import *
from chaosindy.common.cli.batch_builder import BatchBuilder
from chaosindy.common.cli.cli_runner import CliRunner
from chaosindy.common.cli.commands import cmd_open_wallet, \
    cmd_open_pool_and_wallet, cmd_create_local_did, cmd_create_ledger_did, \
    cmd_use_did, cmd_load_plugin, cmd_create_payment_address
from logzero import logger

from chaosindy.common.cli.commands import cmd_create_pool, cmd_create_wallet

from typing import List

# define exceptions
class Error(Exception):
   """Base class for other exceptions"""
   pass

class BatchExecutionFailedException(Error):
   """
   Raised when 'Batch execution failed' encountered when executing Indy CLI
   batch scripts
   """
   pass

def batch_execution_failed(std_out):
    status = get_indy_cli_command_output(std_out,
                                         "Batch execution failed",
                                         return_line_offset=0)
    if status:
        logger.warn("CLI batch execution failed, see out file for more info")
        return True
    else:
        return False


def cli_create_pool(output_dir,
                    pool_name: str,
                    genesis_path: str) -> bool:
    """
    Builds batch and runs batch on Indy CLI to create a pool

    :param output_dir:
    :param pool_name:
    :param genesis_path:
    :return:
    """
    logger.info("Creating a Pool with CLI")

    batch = BatchBuilder()
    batch = cmd_create_pool(batch, pool_name, genesis_path)

    batch_str = batch.build()

    runner = CliRunner(output_dir)
    std_out = runner.run(batch_str, "indy-cli-create-pool").std_out

    if batch_execution_failed(std_out):
        pool_already_exists = get_indy_cli_command_output(std_out,
            "\"{}\" already exists".format(pool_name), return_line_offset=0)
        if not pool_already_exists:
            return False

    return True


def cli_create_wallet(output_dir,
                      wallet_name: str,
                      wallet_key: str=None) -> bool:
    """
    Builds batch and runs batch on Indy CLI to create a wallet

    :param output_dir:
    :param wallet_name:
    :param wallet_key:
    :return:
    """
    logger.info("Creating a Wallet with CLI")

    batch = BatchBuilder()
    cmd_create_wallet(batch, wallet_name, wallet_key)

    batch_str = batch.build()

    runner = CliRunner(output_dir)
    std_out = runner.run(batch_str, "indy-cli-create-wallet").std_out

    if batch_execution_failed(std_out):
        wallet_already_exists = get_indy_cli_command_output(
            std_out, "\"{}\" already exists".format(wallet_name),
            return_line_offset=0)
        if not wallet_already_exists:
            return False

    return True


def cli_create_local_did(output_dir: str,
                         did_seed: str,
                         wallet_name: str,
                         wallet_key: str=None,
                         did_metadata: str=None) -> bool:
    """
    Builds batch and runs batch on Indy CLI to create a DID in the local wallet

    :param output_dir:
    :param did_seed:
    :param wallet_name:
    :param wallet_key:
    :param did_metadata:
    :return:
    """
    logger.info("Creating a local DID with CLI")

    batch = BatchBuilder()
    with cmd_open_wallet(batch, wallet_name, wallet_key=wallet_key):
        cmd_create_local_did(batch, did_seed, metadata=did_metadata)

    batch_str = batch.build()

    runner = CliRunner(output_dir)
    std_out = runner.run(batch_str, "indy-cli-create-local-did").std_out

    if batch_execution_failed(std_out):
        return False

    return True


def cli_create_ledger_did(output_dir: str,
                          sending_did: str,
                          did: str,
                          did_verkey: str,
                          did_seed: str,
                          did_role: str,
                          pool_name: str,
                          wallet_name: str,
                          wallet_key: str=None,
                          did_metadata: str=None) -> bool:
    """
    Builds batch and runs batch on Indy CLI to create a DID on the ledger

    :param output_dir:
    :param sending_did:
    :param did:
    :param did_verkey:
    :param did_seed:
    :param did_role:
    :param pool_name:
    :param wallet_name:
    :param wallet_key:
    :param did_metadata:
    :return:
    """
    logger.info("Creating a DID on the ledger with CLI")

    batch = BatchBuilder()
    with cmd_open_pool_and_wallet(batch,
                                  pool_name,
                                  wallet_name,
                                  wallet_key=wallet_key):
        cmd_create_ledger_did(batch, sending_did, did, did_verkey,
                              seed=did_seed, metadata=did_metadata,
                              role=did_role)

    batch_str = batch.build()

    runner = CliRunner(output_dir)
    std_out = runner.run(batch_str, "indy-cli-create-ledger-did").std_out

    if batch_execution_failed(std_out):
        return False

    return True


def cli_create_payment_address(output_dir: str,
                               address_seed: str,
                               payment_method: str,
                               payment_lib: str,
                               payment_lib_initializer: str,
                               wallet_name: str,
                               wallet_key) -> bool:
    """
    Builds batch and runs batch on Indy CLI to create a payment address

    :param output_dir:
    :param address_seed:
    :param payment_method:
    :param payment_lib:
    :param payment_lib_initializer:
    :param wallet_name:
    :param wallet_key:
    :return:
    """
    logger.info("Creating a payment address with CLI")

    batch = BatchBuilder()
    with cmd_open_wallet(batch, wallet_name, wallet_key=wallet_key):
        cmd_load_plugin(batch, payment_lib, payment_lib_initializer)
        cmd_create_payment_address(batch,
                                   payment_method,
                                   address_seed=address_seed)

    batch_str = batch.build()

    runner = CliRunner(output_dir)
    std_out = runner.run(batch_str, "indy-cli-create-payment-address").std_out

    if batch_execution_failed(std_out):
        return False

    return True


def cli_mint_tokens(output_dir: str,
                    sending_did: str,
                    trustee_did_list: str,
                    payment_address: str,
                    token_num: str,
                    payment_lib: str,
                    payment_lib_initializer: str,
                    pool_name: str,
                    wallet_name: str,
                    wallet_key: str=None
                   ):

    """
    Builds batch and runs batch on Indy CLI to mint tokens
    :param output_dir:
    :param sending_did:
    :param trustee_did_list:
    :param payment_address:
    :param token_num:
    :param payment_lib:
    :param payment_lib_initializer:
    :param pool_name:
    :param wallet_name:
    :param wallet_key:
    :return:
    """
    logger.info("Minting tokens with CLI")

    batch = BatchBuilder()
    with cmd_open_wallet(batch, wallet_name, wallet_key=wallet_key):
        cmd_load_plugin(batch, payment_lib, payment_lib_initializer)
        cmd_use_did(batch, sending_did)
        batch.add_command("ledger mint-prepare outputs=({},{})".format(
            payment_address, token_num))

    batch_str = batch.build()

    std_out = CliRunner(output_dir).run(batch_str,
                                        "indy-cli-prepare-mint").std_out

    mint_txn = get_indy_cli_command_output(std_out,
                                           "MINT transaction has been created:")
    if isinstance(mint_txn, str):
        mint_txn = mint_txn.strip()

    for trustee_did in trustee_did_list:
        batch = BatchBuilder()
        with cmd_open_wallet(batch, wallet_name, wallet_key=wallet_key):
            cmd_load_plugin(batch, payment_lib, payment_lib_initializer)
            cmd_use_did(batch, trustee_did)
            batch.add_command("ledger sign-multi txn={}\n".format(mint_txn))

        batch_str = batch.build()

        std_out = CliRunner(output_dir).run(batch_str,
                                            "indy-cli-sign-mint").std_out

        if batch_execution_failed(std_out):
            return False

        mint_txn = get_indy_cli_command_output(std_out,
                                               "Transaction has been signed",
                                               return_line_offset=1)
        if isinstance(mint_txn, str):
            mint_txn = mint_txn.strip()

    batch = BatchBuilder()
    with cmd_open_pool_and_wallet(batch,
                                  pool_name,
                                  wallet_name,
                                  wallet_key=wallet_key):
        cmd_use_did(batch, sending_did)
        batch.add_command("ledger custom {}".format(mint_txn))

    batch_str = batch.build()

    std_out = CliRunner(output_dir).run(batch_str,
                                        "indy-cli-submit-mint").std_out

    if batch_execution_failed(std_out):
        return False

    return True


def cli_get_payment_addresses(output_dir: str,
                              wallet_name: str,
                              wallet_key: str=None,
                              payment_scheme: str="pay",
                              payment_method: str="null"
                             ) -> List[str]:

    """
    Builds batch and runs batch on Indy CLI to get a list of payment addresses
    from a wallet
    :param output_dir: str
    :param wallet_name: str
    :param wallet_key: str
    :payment_scheme: str="pay"
    :payment_method: str="null"
    :return: List[str]
    """
    logger.debug("Getting payment addresses from wallet %s", wallet_name)

    batch = BatchBuilder()
    with cmd_open_wallet(batch, wallet_name, wallet_key=wallet_key):
        batch.add_command("payment-address list\n")

    batch_str = batch.build()

    std_out = CliRunner(output_dir).run(batch_str,
                                        "indy-cli-payment-address-list").std_out

    payment_address_list = []
    if batch_execution_failed(std_out):
        raise BatchExecutionFailedException
    else:
        payment_address_list = get_indy_cli_command_output(std_out,
            "{}:{}:".format(payment_scheme, payment_method),
            return_line_offset=0, multi=True)
    return parse_payment_addresses(payment_address_list, "|", 1)


def cli_generate_payment_addresses(output_dir: str,
                                   payment_lib: str,
                                   payment_lib_initializer: str,
                                   wallet_name: str,
                                   wallet_key: str=None,
                                   payment_method: str="null",
                                   number_of_addresses: Union[int,str]=1
                             ) -> List[str]:

    """
    Builds batch and runs batch on Indy CLI to generate a given number of
    payment addresses in the given wallet
    :param output_dir: str
    :payment_lib: str
    :payment_lib_initializer: str
    :param wallet_name: str
    :param wallet_key: str=None
    :payment_method: str="null"
    :number_of_addresses: Union[int,str]=1
    :return: List[str]
    """
    logger.info("Getting payment addresses from wallet %s", wallet_name)

    batch = BatchBuilder()
    with cmd_open_wallet(batch, wallet_name, wallet_key=wallet_key):
        cmd_load_plugin(batch, payment_lib, payment_lib_initializer)
        for i in range(0, int(number_of_addresses)):
            batch.add_command(
                "payment-address create payment_method={}\n".format(
                payment_method))

    batch_str = batch.build()

    std_out = CliRunner(output_dir).run(batch_str,
        "indy-cli-payment-address-generate").std_out

    payment_address_generate = []
    if batch_execution_failed(std_out):
        raise BatchExecutionFailedException
    else:
        payment_address_generate = get_indy_cli_command_output(std_out,
            "Payment Address has been created", return_line_offset=0,
            multi=True)
    return parse_payment_addresses(payment_address_generate, "\"", 1)


def cli_get_payment_sources(output_dir: str,
                            from_payment_addresses: List[str],
                            payment_lib: str,
                            payment_lib_initializer: str,
                            pool_name: str,
                            wallet_name: str,
                            wallet_key: str=None,
                            payment_method: str='null'
                            ) -> List[str]:

    """
    Builds batch and runs batch on Indy CLI to get list of payment sources from
    a list of payment addresses.
    :param output_dir: str
    :param from_payment_addresses: List[str]
    :payment_lib: str
    :payment_lib_initializer: str
    :param pool_name: str
    :param wallet_name: str
    :param wallet_key: str=None
    :payment_method: str="null"
    :return: List[str]
    """
    logger.info("Getting payment sources from addresses in wallet %s",
                wallet_name)

    batch = BatchBuilder()
    with cmd_open_pool_and_wallet(batch,
                                  pool_name,
                                  wallet_name,
                                  wallet_key=wallet_key):
        cmd_load_plugin(batch, payment_lib, payment_lib_initializer)
        for payment_address in from_payment_addresses:
            logger.info("Getting payment sources from address %s",
                        payment_address)
            batch.add_command(
                "ledger get-payment-sources payment_address={}\n".format(
                payment_address))

    batch_str = batch.build()

    std_out = CliRunner(output_dir).run(batch_str,
                                        "indy-cli-payment-sources-get").std_out

    payment_address_sources = []
    if batch_execution_failed(std_out):
        raise BatchExecutionFailedException
    else:
        payment_address_sources = get_indy_cli_command_output(std_out,
            "txo:{}".format(payment_method), return_line_offset=0,
            multi=True)
    return parse_payment_sources(payment_address_sources)
