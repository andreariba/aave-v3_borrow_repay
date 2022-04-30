from scripts.utility import get_account
from scripts.get_weth import get_weth
from brownie import network, config, interface
from web3 import Web3

amount = Web3.toWei(0.01, "ether")


def main():
    account = get_account()
    active_network = network.show_active()
    erc20_address = config["networks"][active_network]["weth_token"]

    if active_network == "mainnet-fork":
        get_weth()
    # ABI
    # address
    pool = get_pool(account, active_network)
    print(pool)

    # approve sending our ERC20 token by calling the function approve()
    # since we will do it a lot, a function approve_erc20() is created
    approve_erc20(pool.address, amount, erc20_address, account)
    print("WETH ERC20 approved")

    # from the IPool interface
    # pool.deposit(
    #     address asset, -> erc20_address
    #     uint256 amount, -> amount of erc20 to deposit
    #     address onBehalfOf, -> account
    #     uint16 referralCode -> deprecated not used usually set to 0
    # )
    tx = pool.supply(erc20_address, amount, account.address, 0, {"from": account})
    tx.wait(1)
    print("WETH deposited")

    # now i can borrow, but how much?
    collateral, debt, borrowable = get_borrowable_data(pool, account)

    # DAI / ETH
    dai_eth_price = get_asset_price(
        config["networks"][active_network]["dai_eth_price_feed"]
    )
    print("Latest DAI/ETH price: ", dai_eth_price)

    # how much dai I'd like to borrow
    amount_to_borrow = 0.5 * borrowable / dai_eth_price
    amount_to_borrow_wei = Web3.toWei(amount_to_borrow, "ether")
    print(f"Borrow {amount_to_borrow} DAI -> {amount_to_borrow_wei}")

    # pool.borrow(
    #     address asset, -> DAI address
    #     uint256 amount, -> amount
    #     uint256 interestRateMode, -> 1 or 2, for stable or variable
    #     uint16 referralCode, ->
    #     address onBehalfOf -> my address: account.address
    # )
    dai_token_address = config["networks"][active_network]["dai_token"]

    borrow_tx = pool.borrow(
        dai_token_address,
        amount_to_borrow_wei,
        1,
        0,
        account.address,
        {"from": account},
    )

    borrow_tx.wait(1)
    print(f"Borrowed {amount_to_borrow_wei} DAI")

    collateral, debt, borrowable = get_borrowable_data(pool, account)

    debt_wei = Web3.toWei(collateral / dai_eth_price, "ether")
    # debt_wei = Web3.toWei(debt, "ether")

    # repay all the debts
    repay_all(pool, account, debt_wei)

    print(f"Repayed {debt_wei} DAI")

    get_borrowable_data(pool, account)

    return


def repay_all(pool, account, amount=-1):
    approve_erc20(
        pool,
        amount,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )

    tx = pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )
    tx.wait(1)
    return


def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    decimals = dai_eth_price_feed.decimals()
    return float(latest_price) / 10**decimals


def get_borrowable_data(pool, account):

    # get the pool data from the account user
    (
        total_collateral_base,
        total_debt_base,
        available_borrows_base,
        current_liquidation_threshold,
        loan_to_value,
        health_factor,
    ) = pool.getUserAccountData(account.address)

    # convert wei to eth
    # print(f"Collateral: {total_collateral_base}")
    # print(f"Debt: {total_debt_base}")
    # print(f"Available: {available_borrows_base}")
    print(f"Current liquidation threshold: {current_liquidation_threshold}")
    print(f"LTV: {loan_to_value}")
    print(f"Health factor: {health_factor}")

    # aave v3 takes the price feeds from chainlink so decimals are only 8
    # total_collateral_eth = Web3.fromWei(total_collateral_base, "ether")
    # total_debt_eth = Web3.fromWei(total_debt_base, "ether")
    # available_borrows_eth = Web3.fromWei(available_borrows_base, "ether")

    # improve by asking chainlink aggregator the decimals
    total_collateral_eth = float(total_collateral_base) / 10**12
    total_debt_eth = float(total_debt_base) / 10**12
    available_borrows_eth = float(available_borrows_base) / 10**12
    print(f"Collateral: {total_collateral_eth} ETH")
    print(f"Debt: {total_debt_eth} ETH")
    print(f"Available: {available_borrows_eth} ETH")

    return (
        float(total_collateral_eth),
        float(total_debt_eth),
        float(available_borrows_eth),
    )


def approve_erc20(spender, amount, token_address, account):
    # approving an ERC20 token
    erc20 = interface.IERC20(token_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    return erc20


def get_pool(account, active_network):
    pool_address_provider = interface.IPoolAddressesProvider(
        config["networks"][active_network].get("pool_addresses_provider")
    )
    # get the pool address from the provider
    pool_address = pool_address_provider.getPool()

    # connect to the pool through the interface
    pool = interface.IPool(pool_address)

    return pool
