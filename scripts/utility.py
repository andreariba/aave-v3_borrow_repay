from brownie import network, accounts, config


DEVELOPMENT_BLOCKCHAINS = ["mainnet-fork", "development", "polygon-mainnet-fork"]
FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]


def get_account(index=None, id=None):

    # managing the cases:

    # 1. if index -> accounts[index]
    if index:
        return accounts[index]

    # 2. if id -> accounts from id (e.g. metamask)
    if id:
        return accounts.load(id)

    # 3. if local environments -> accounts[0]
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]

    # 4. testnet -> config.wallets.from_key
    return accounts.add(config["wallets"]["from_key"])
