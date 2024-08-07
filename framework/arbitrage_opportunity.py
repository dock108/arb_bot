import time
import logging

# Initialize logger
logger = logging.getLogger('ArbitrageBot')

class ArbitrageOpportunity:
    """
    ArbitrageOpportunity class to handle the detection and execution of arbitrage opportunities.

    This class identifies potential arbitrage opportunities across exchanges, evaluates their
    viability, and executes trades if profitable.
    """

    def __init__(self):
        """
        Initialize the ArbitrageOpportunity with cooldown tracking and account management.

        """
        
    def find_arbitrage_opportunities(self, prices, buy_exchange, sell_exchange):
        """
        Find all potential arbitrage opportunities across exchanges.

        This method scans through the provided price data, comparing prices for each currency pair 
        across different exchanges to identify potential arbitrage opportunities.

        Parameters:
        - prices (dict): A dictionary containing the current prices of trading pairs on various exchanges.
        - buy_exchange (str): The name of the exchange to buy from.
        - sell_exchange (str): The name of the exchange to sell to.

        Returns:
        - List[dict]: A list of potential arbitrage opportunities, each represented as a dictionary.
        """
        opportunities = []
        current_time = time.time()

        # Check if the buy exchange is on cooldown
        if current_time < self.cooldown_tracker.get(buy_exchange, 0):
            logger.debug(f"{buy_exchange} is on cooldown. Skipping opportunities for this exchange.")
            return opportunities

        # Iterate over each currency pair available on the buy exchange
        for pair in prices[buy_exchange]:
            if pair in prices[sell_exchange]:  # Check if the pair exists on the sell exchange
                buy_price = prices[buy_exchange][pair]
                sell_price = prices[sell_exchange][pair]

                # Handle None values in prices
                if buy_price is None or sell_price is None:
                    logger.debug(f"Skipping {pair} due to NoneType prices.")
                    continue

                # Calculate gross profit percentage
                gross_profit_percentage = self.calculate_gross_profit(buy_price, sell_price)
                # If there is a positive gross profit, it's a potential opportunity
                if gross_profit_percentage > 0:
                    opportunity = {
                        'datetime': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'buy_exchange': buy_exchange,
                        'sell_exchange': sell_exchange,
                        'buy_pair': pair,
                        'sell_pair': pair,
                        'buy_price': buy_price,
                        'sell_price': sell_price,
                        'gross_profit_percentage': gross_profit_percentage
                    }
                    opportunities.append(opportunity)
                    logger.debug(f"Potential arbitrage opportunity found: {opportunity}")

        return opportunities

    def calculate_gross_profit(self, buy_price, sell_price):
        """
        Calculate the gross profit percentage for a given trade.

        This method computes the potential profit from buying on one exchange and selling on another.

        Parameters:
        - buy_price (float): The price of the asset on the buy exchange.
        - sell_price (float): The price of the asset on the sell exchange.

        Returns:
        - float: The calculated gross profit percentage.
        """
        return ((sell_price - buy_price) / buy_price) * 100
