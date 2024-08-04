import logging
import csv

# Initialize logger
logger = logging.getLogger('ArbitrageBot')

class AccountManager:
    """
    AccountManager class to handle account operations for arbitrage trading.

    This class manages account balances, tracks fees and taxes, and handles rebalancing of account funds.
    """

    def __init__(self, initial_account_value, exchanges, average_fee=0.002867):
        """
        Initialize the AccountManager with account values and exchange information.

        Parameters:
        - initial_account_value (float): The initial total value of the account to be distributed across exchanges.
        - exchanges (list): A list of exchange names that the account manager will interact with.
        - average_fee (float): The average trading fee percentage for transactions.

        Attributes:
        - average_fee (float): The average trading fee percentage for transactions.
        - exchanges (list): List of exchange names.
        - account_values (dict): A dictionary storing account balances for each exchange.
        - tax_tally (float): Accumulated tax tally for profits.
        - fees_tally (float): Accumulated fees tally for transactions.
        - money_out_tally (float): Accumulated tally of funds removed from the account.
        """
        logger.debug("Initializing AccountManager.")
        self.average_fee = average_fee  # 0.2867% trading fee
        self.exchanges = exchanges
        self.account_values = {exchange: initial_account_value / len(exchanges) for exchange in exchanges}
        self.tax_tally = 0
        self.fees_tally = 0
        self.money_out_tally = 0
        logger.debug(f"Initial account values: {self.account_values}")

    def rebalance_accounts(self):
        """
        Rebalance account values evenly across all exchanges.

        This method calculates the total value across all exchanges and redistributes it evenly,
        ensuring that each exchange has the same amount of funds. This is done to maintain equal
        trading power across exchanges and maximize potential arbitrage opportunities.
        """
        logger.debug("Rebalancing accounts.")
        total_value = sum(self.account_values.values())
        avg_value = total_value / len(self.exchanges)  # Calculate the average value per exchange
        for exchange in self.exchanges:
            self.account_values[exchange] = avg_value
        logger.info(f"Rebalanced account values: {self.account_values}")

    def update_account_values(self, buy_exchange, sell_exchange, trade_value, net_profit):
        """
        Update account values after executing a trade and rebalance accounts.

        This method adjusts the account balances on the buy and sell exchanges and rebalances
        the total account value across all exchanges.

        Parameters:
        - buy_exchange (str): The name of the exchange where the asset was purchased.
        - sell_exchange (str): The name of the exchange where the asset was sold.
        - trade_value (float): The value of the trade being executed.
        - net_profit (float): The net profit from the trade.
        """
        # Deduct the trade value from the buy exchange and add it to the sell exchange
        self.account_values[buy_exchange] -= trade_value
        self.account_values[sell_exchange] += trade_value + net_profit
        logger.info(f"Updated account values: {self.account_values}")

        # Rebalance the accounts to evenly distribute funds
        self.rebalance_accounts()

        # Log financial details of the trade
        logger.info(f"Net Profit: ${net_profit:.2f}")
        logger.info(f"Total Taxes: ${self.tax_tally:.2f}")
        logger.info(f"Total Fees: ${self.fees_tally:.2f}")
        logger.info(f"Total Money Out: ${self.money_out_tally:.2f}")

    def log_opportunity(self, opportunity, net_profit):
        """
        Log an arbitrage opportunity to a CSV file for historical tracking.

        This method records the details of each arbitrage opportunity, including the exchanges involved,
        the trading pairs, the prices, and the net profit achieved.

        Parameters:
        - opportunity (dict): A dictionary containing the details of the arbitrage opportunity.
        - net_profit (float): The net profit obtained from the arbitrage trade.
        """
        logger.info("Logging arbitrage opportunity.")
        logger.debug(f"Opportunity details: {opportunity}, Net Profit: {net_profit}")
        with open('historical_opportunities.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                opportunity['datetime'],
                opportunity['buy_exchange'],
                opportunity['sell_exchange'],
                opportunity['buy_pair'],
                opportunity['sell_pair'],
                opportunity['buy_price'],
                opportunity['sell_price'],
                opportunity['gross_profit_percentage'],
                net_profit
            ])
