import time
import logging
from framework.exchange_manager import ExchangeManager
from framework.account_manager import AccountManager
from framework.arbitrage_opportunity import ArbitrageOpportunity
from framework.profit_calculator import ProfitCalculator

# Initialize logger
logger = logging.getLogger('ArbitrageBot')

class ArbitrageFramework:
    """
    ArbitrageFramework class to manage the overall arbitrage trading strategy across multiple exchanges.

    This class coordinates the fetching of prices, checking for arbitrage opportunities, managing accounts,
    and executing trades, while calculating potential profits and updating account values.
    """

    def __init__(self, initial_account_value, exchanges):
        """
        Initialize the ArbitrageFramework with account values and exchange information.

        Parameters:
        - initial_account_value (float): The initial total value of the account to be distributed across exchanges.
        - exchanges (dict): A dictionary of exchange names mapped to ccxt exchange objects.

        Attributes:
        - exchange_manager (ExchangeManager): Manages the fetching of price data from exchanges.
        - account_manager (AccountManager): Manages the account balances and rebalancing across exchanges.
        - profit_calculator (ProfitCalculator): Calculates potential profits from trades.
        - cooldown_tracker (dict): Tracks cooldown status for each exchange to prevent rapid successive trades.
        """
        logger.debug("Initializing ArbitrageFramework.")

        self.exchange_manager = ExchangeManager(exchanges)
        self.account_manager = AccountManager(initial_account_value, exchanges)
        self.profit_calculator = ProfitCalculator()
        self.cooldown_tracker = {exchange: 0 for exchange in exchanges.keys()}

        logger.debug(f"Initial account values: {self.account_manager.account_values}")

    def run(self):
        """
        Main method to run the arbitrage framework, fetching prices and checking for arbitrage opportunities.
        """
        logger.debug("Running arbitrage framework.")

        # Fetch real-time prices from exchanges
        prices = self.exchange_manager.get_real_time_prices()

        # Check for arbitrage opportunities
        opportunities = self.check_real_time_arbitrage(prices)

        if opportunities:
            # Execute the best opportunity if available
            self.execute_best_opportunity(opportunities)
        else:
            logger.debug("No arbitrage opportunity found.")

    def check_real_time_arbitrage(self, prices):
        """
        Check for real-time arbitrage opportunities across multiple exchanges.

        Parameters:
        - prices (dict): A dictionary containing the current prices of trading pairs on various exchanges.

        Returns:
        - List[dict]: A list of arbitrage opportunities identified.
        """
        logger.debug("Checking for real-time arbitrage opportunities.")

        opportunities = []

        for buy_exchange in prices:
            for sell_exchange in prices:
                if buy_exchange != sell_exchange:
                    # Create ArbitrageOpportunity instances for each potential opportunity
                    arbitrage_opportunity = ArbitrageOpportunity(self.cooldown_tracker, self.account_manager)
                    opportunities.extend(arbitrage_opportunity.find_arbitrage_opportunities(prices, buy_exchange, sell_exchange))

        return opportunities

    def execute_best_opportunity(self, opportunities):
        """
        Evaluate and execute the best arbitrage opportunity if viable.

        This method assesses the best opportunity for viability based on the gross profit percentage
        and cooldown status, executing the trade if criteria are met.

        Parameters:
        - opportunities (List[dict]): A list of arbitrage opportunities.
        """
        # Find the best opportunity
        best_opportunity = max(opportunities, key=lambda x: x['gross_profit_percentage'])

        # Check if the opportunity is profitable and the buy exchange is not on cooldown
        if best_opportunity['gross_profit_percentage'] > 1 and time.time() > self.cooldown_tracker[best_opportunity['buy_exchange']]:
            self.execute_trade(best_opportunity)
            logger.info("Arbitrage opportunity executed successfully.")
        else:
            logger.debug("No viable arbitrage opportunity or exchange is on cooldown.")

    def execute_trade(self, opportunity):
        """
        Execute the trade for a given arbitrage opportunity.

        This method performs the trade, logging the details and updating account balances accordingly.

        Parameters:
        - opportunity (dict): A dictionary representing the arbitrage opportunity.
        """
        logger.info("Arbitrage Opportunity Found:")
        logger.info(f"Buy {opportunity['buy_pair']} on {opportunity['buy_exchange']} at ${opportunity['buy_price']:.2f}")
        logger.info(f"Sell {opportunity['sell_pair']} on {opportunity['sell_exchange']} at ${opportunity['sell_price']:.2f}")
        logger.info(f"Gross Profit: {opportunity['gross_profit_percentage']:.2f}%")

        # Calculate net profit after fees and taxes
        trade_value = self.account_manager.account_values[opportunity['buy_exchange']]
        gross_profit = trade_value * (opportunity['gross_profit_percentage'] / 100)
        net_profit, fees, taxes = self.profit_calculator.calculate_net_profit(gross_profit, trade_value)

        # Update account values and rebalance
        self.account_manager.update_account_values(opportunity['buy_exchange'], opportunity['sell_exchange'], trade_value, net_profit)

        # Log the opportunity
        self.account_manager.log_opportunity(opportunity, net_profit)

        # Set cooldown for the buy exchange to prevent frequent trading
        self.cooldown_tracker[opportunity['buy_exchange']] = time.time() + 120  # 2 minutes cooldown
        logger.debug(f"Set cooldown for {opportunity['buy_exchange']}")
