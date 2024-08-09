import time
import logging
from config.config import COOLDOWN_HOURS, MINIMUM_BALANCES

# Initialize logger
logger = logging.getLogger('ArbitrageBot')

class ArbitrageOpportunity:
    """
    ArbitrageOpportunity class to handle the detection and execution of arbitrage opportunities.
    """

    def __init__(self):
        """
        Initialize the ArbitrageOpportunity with cooldown tracking and account management.
        """
        self.cooldown_tracker = {}

    def find_arbitrage_opportunities(self, prices, buy_exchange, sell_exchange):
        """
        Find all potential arbitrage opportunities across exchanges.
        """
        opportunities = []

        for pair in prices[buy_exchange]:
            if pair in prices[sell_exchange]:
                buy_price, sell_price = self.get_prices_for_pair(prices, buy_exchange, sell_exchange, pair)
                
                if self.is_valid_price_pair(buy_price, sell_price):
                    gross_profit_percentage = self.calculate_gross_profit(buy_price, sell_price)
                    if gross_profit_percentage > 0:
                        opportunity = self.create_opportunity(buy_exchange, sell_exchange, pair, buy_price, sell_price, gross_profit_percentage)
                        opportunities.append(opportunity)
                        logger.debug(f"Potential arbitrage opportunity found: {opportunity}")

        return opportunities

    def get_prices_for_pair(self, prices, buy_exchange, sell_exchange, pair):
        """
        Retrieve the buy and sell prices for a given trading pair across exchanges.

        Parameters:
        - prices (dict): Dictionary of prices from different exchanges.
        - buy_exchange (str): The exchange to buy from.
        - sell_exchange (str): The exchange to sell on.
        - pair (str): The trading pair.

        Returns:
        - tuple: The buy price and sell price.
        """
        buy_price = prices[buy_exchange][pair].get('ask')
        sell_price = prices[sell_exchange][pair].get('bid')
        return buy_price, sell_price

    def is_valid_price_pair(self, buy_price, sell_price):
        """
        Validate if the buy and sell prices are not None.

        Parameters:
        - buy_price (float): The price to buy.
        - sell_price (float): The price to sell.

        Returns:
        - bool: True if both prices are valid, otherwise False.
        """
        if buy_price is None or sell_price is None:
            logger.debug("Skipping pair due to NoneType prices.")
            return False
        return True

    def create_opportunity(self, buy_exchange, sell_exchange, pair, buy_price, sell_price, gross_profit_percentage):
        """
        Create an arbitrage opportunity dictionary.

        Parameters:
        - buy_exchange (str): The exchange to buy from.
        - sell_exchange (str): The exchange to sell on.
        - pair (str): The trading pair.
        - buy_price (float): The price to buy.
        - sell_price (float): The price to sell.
        - gross_profit_percentage (float): The calculated gross profit percentage.

        Returns:
        - dict: A dictionary representing the arbitrage opportunity.
        """
        return {
            'datetime': time.strftime("%Y-%m-%d %H:%M:%S"),
            'buy_exchange': buy_exchange,
            'sell_exchange': sell_exchange,
            'buy_pair': pair,
            'sell_pair': pair,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'gross_profit_percentage': gross_profit_percentage
        }

    def calculate_gross_profit(self, buy_price, sell_price):
        """
        Calculate the gross profit percentage for a given trade.
        """
        return ((sell_price - buy_price) / buy_price) * 100

    def execute_trade(self, opportunity, exchanges):
        """
        Execute the trade for a given arbitrage opportunity using bid and ask prices.
        """
        logger.info(f"Executing trade for opportunity: {opportunity}")

        buy_exchange, sell_exchange, buy_pair, sell_pair, buy_price, sell_price = self.extract_opportunity_details(opportunity)
        buy_currency, sell_currency = self.get_currencies_from_pairs(buy_pair, sell_pair)

        buy_balance = self.get_balance(exchanges, buy_exchange, buy_currency)
        sell_balance = self.get_balance(exchanges, sell_exchange, sell_currency)

        if self.is_sufficient_balance(buy_balance, sell_balance, buy_currency, sell_currency):
            return self.execute_orders(exchanges, buy_exchange, sell_exchange, buy_pair, sell_pair, buy_price, sell_price, buy_balance, sell_balance)
        else:
            logger.info("Insufficient balance for trade execution.")
            return False

    def extract_opportunity_details(self, opportunity):
        """
        Extract details from the arbitrage opportunity.

        Parameters:
        - opportunity (dict): The arbitrage opportunity.

        Returns:
        - tuple: Contains buy_exchange, sell_exchange, buy_pair, sell_pair, buy_price, and sell_price.
        """
        buy_exchange = opportunity['buy_exchange']
        sell_exchange = opportunity['sell_exchange']
        buy_pair = opportunity['buy_pair']
        sell_pair = opportunity['sell_pair']
        buy_price = opportunity['buy_price']
        sell_price = opportunity['sell_price']
        return buy_exchange, sell_exchange, buy_pair, sell_pair, buy_price, sell_price

    def get_currencies_from_pairs(self, buy_pair, sell_pair):
        """
        Extract the base currencies from the trading pairs.

        Parameters:
        - buy_pair (str): The buy trading pair (e.g., 'BTC/ETH').
        - sell_pair (str): The sell trading pair (e.g., 'ETH/BTC').

        Returns:
        - tuple: Contains the base currencies for the buy and sell pairs.
        """
        buy_currency = buy_pair.split('/')[0]
        sell_currency = sell_pair.split('/')[0]
        return buy_currency, sell_currency

    def is_sufficient_balance(self, buy_balance, sell_balance, buy_currency, sell_currency):
        """
        Check if there is sufficient balance to execute the trade.

        Parameters:
        - buy_balance (float): The balance available for buying.
        - sell_balance (float): The balance available for selling.
        - buy_currency (str): The currency being bought.
        - sell_currency (str): The currency being sold.

        Returns:
        - bool: True if both balances are sufficient, False otherwise.
        """
        min_balances = MINIMUM_BALANCES
        if buy_balance >= min_balances.get(buy_currency, 0) and sell_balance >= min_balances.get(sell_currency, 0):
            return True
        return False

    def execute_orders(self, exchanges, buy_exchange, sell_exchange, buy_pair, sell_pair, buy_price, sell_price, buy_balance, sell_balance):
        """
        Execute the buy and sell orders on the respective exchanges.

        Parameters:
        - exchanges (dict): Dictionary of exchange objects.
        - buy_exchange (str): The exchange to buy from.
        - sell_exchange (str): The exchange to sell on.
        - buy_pair (str): The trading pair to buy.
        - sell_pair (str): The trading pair to sell.
        - buy_price (float): The price to buy at.
        - sell_price (float): The price to sell at.
        - buy_balance (float): The balance available for buying.
        - sell_balance (float): The balance available for selling.

        Returns:
        - bool: True if the orders were executed successfully, False otherwise.
        """
        try:
            trade_amount = min(buy_balance, sell_balance)

            buy_order = exchanges[buy_exchange].create_order(
                symbol=buy_pair,
                type='market',
                side='buy',
                amount=trade_amount,
                price=buy_price
            )
            logger.info(f"Buy order executed: {buy_order}")

            sell_order = exchanges[sell_exchange].create_order(
                symbol=sell_pair,
                type='market',
                side='sell',
                amount=trade_amount,
                price=sell_price
            )
            logger.info(f"Sell order executed: {sell_order}")

            self.update_cooldown_tracker(buy_pair, sell_pair, trade_amount, buy_balance)

            return True
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return False

    def update_cooldown_tracker(self, buy_pair, sell_pair, trade_amount, buy_balance):
        """
        Update the cooldown tracker for the traded currencies.

        Parameters:
        - buy_pair (str): The trading pair that was bought.
        - sell_pair (str): The trading pair that was sold.
        - trade_amount (float): The amount of the currency traded.
        - buy_balance (float): The balance available for buying.
        """
        buy_currency = buy_pair.split('/')[0]
        sell_currency = sell_pair.split('/')[0]

        cooldown_currency = buy_currency if trade_amount == buy_balance else sell_currency
        cooldown_hours = COOLDOWN_HOURS
        self.cooldown_tracker[cooldown_currency] = time.time() + 3600 * cooldown_hours
