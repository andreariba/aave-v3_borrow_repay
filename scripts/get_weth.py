from distutils.command.config import config
from scripts.utility import get_account
from brownie import interface, config, network
from web3 import Web3


def get_weth():

    """
    Mints WETH by sending ETH
    """
    account = get_account()

    active_network = network.show_active()

    weth = interface.IWETH(config["networks"][active_network].get("weth_token"))

    tx = weth.deposit({"from": account, "value": Web3.toWei(0.1, "ether")})
    print("I should have 0.1 WETH")
    tx.wait(1)
    return tx


def main():
    get_weth()
    return
