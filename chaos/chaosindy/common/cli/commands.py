import os, subprocess
from contextlib import contextmanager
from logzero import logger

from chaosindy.common.cli.batch_builder import BatchBuilder

# TODO Most of these could be rolled up to indy chaos


def _add_parameter(cmd, key, value, check_bool=True):
    if check_bool is not None:
        cmd = cmd + " {}=\"{}\"".format(str(key), str(value))
        return cmd
    else:
        return cmd


def cmd_create_wallet(builder: BatchBuilder,
                      wallet_name: str,
                      wallet_key: str) -> BatchBuilder:
    """
    Commands to create a wallet

    :param builder:
    :param wallet_name:
    :param wallet_key:
    :return:
    """

    cmd = "wallet create {}".format(wallet_name)
    if wallet_key:
        cmd = _add_parameter(cmd, "key", wallet_key)
    else:
        cmd = cmd + " key"

    builder.add_command(cmd)

    return builder


def cmd_create_pool(builder: BatchBuilder,
                    pool_name:str,
                    genesis_path: str) -> BatchBuilder:
    """
    Commands to create a pool

    :param builder:
    :param pool_name:
    :param genesis_path:
    :return:
    """

    cmd = "pool create {}".format(pool_name)
    cmd = _add_parameter(cmd, "gen_txn_file", genesis_path)

    builder.add_command(cmd)

    return builder


@contextmanager
def cmd_open_wallet(builder: BatchBuilder,
                    wallet_name: str,
                    wallet_key: str=None) -> BatchBuilder:
    """
    Commands to open a wallet

    :param builder:
    :param wallet_name:
    :param wallet_key:
    :return:
    """

    builder.add_command("")
    builder.add_command("### OPENING WALLET ###")

    cmd = "wallet open {}".format(wallet_name)
    if wallet_key:
        cmd = _add_parameter(cmd, "key", wallet_key)
    else:
        cmd = cmd + " key"

    builder.add_command(cmd)

    yield builder

    builder.add_command("")
    builder.add_command("### CLOSING WALLET ###")

    builder.add_command("wallet close")

    return builder


@contextmanager
def cmd_open_pool(builder: BatchBuilder, pool_name: str) -> BatchBuilder:
    """
    Commands to connects to a pool. Closes via a context manager

    :param builder:
    :param pool_name:
    :return:
    """
    builder.add_command("")
    builder.add_command("### OPENING POOL ###")

    builder.add_command("pool connect {}".format(pool_name))
    yield builder

    builder.add_command("")
    builder.add_command("### CLOSING POOL ###")

    builder.add_command("pool disconnect")

    return builder


@contextmanager
def cmd_open_pool_and_wallet(builder: BatchBuilder,
                             pool_name: str,
                             wallet_name: str,
                             wallet_key: str=None) -> BatchBuilder:
    """
    Commands to opens a wallet and connects to a pool in one functions (combines the other functions)
    :param builder:
    :param pool_name:
    :param wallet_name:
    :param wallet_key:
    :return:
    """
    with cmd_open_wallet(builder, wallet_name, wallet_key=wallet_key):
        with cmd_open_pool(builder, pool_name):
            yield builder

    return builder


def cmd_use_did(builder: BatchBuilder, did: str):
    """
    Commands to sets the used DID in the CLI

    :param builder:
    :param did:
    :return:
    """
    builder.add_command("did use {}".format(str(did)))

    return builder


def cmd_create_local_did(builder: BatchBuilder,
                         seed: str=None,
                         metadata: str=None) -> BatchBuilder:
    """
    Commands to creates a DID in the local wallet only (it is not created on the ledger)

    :param builder:
    :param seed:
    :param metadata:
    :return:
    """
    cmd = "did new"

    cmd = _add_parameter(cmd, "seed", str(seed), check_bool=(seed is not None))
    cmd = _add_parameter(cmd, "metadata", str(metadata), check_bool=(metadata is not None))

    builder.add_command(cmd)

    return builder


def cmd_create_ledger_did(builder: BatchBuilder,
                          sending_did: str,
                          did: str,
                          did_verkey: str,
                          seed: str=None,
                          metadata: str=None,
                          role: str=None) -> BatchBuilder:
    """
    Commands to create a DID on the ledger in addition to the local wallet

    :param builder:
    :param sending_did:
    :param did:
    :param did_verkey:
    :param seed:
    :param metadata:
    :param role:
    :return:
    """
    cmd_create_local_did(builder, seed=seed, metadata=metadata)
    cmd_use_did(builder, sending_did)

    cmd = "ledger nym"
    cmd = _add_parameter(cmd, "did", str(did))
    cmd = _add_parameter(cmd, "role", str(role), (role is not None))
    cmd = _add_parameter(cmd, "verkey", str(did_verkey), (did_verkey is not None))

    builder.add_command(cmd)

    return builder


def cmd_load_plugin(builder: BatchBuilder,
                    lib_path: str,
                    initializer: str):
    """
    Commands to load and initialize a plugin library

    :param builder:
    :param lib_path:
    :param initializer:
    :return:
    """
    cmd = "load-plugin"

    cmd = _add_parameter(cmd, "library", lib_path)
    cmd = _add_parameter(cmd, "initializer", initializer)

    builder.add_command(cmd)

    return builder


def cmd_create_payment_address(builder: BatchBuilder,
                               payment_method: str,
                               address_seed: str=None):
    """
    Commands to create a payment address

    :param builder:
    :param payment_method:
    :param address_seed:
    :return:
    """
    cmd = "payment-address create"

    cmd = _add_parameter(cmd, "payment_method", payment_method)
    cmd = _add_parameter(cmd, "seed", str(address_seed), (address_seed is not None))

    builder.add_command(cmd)
