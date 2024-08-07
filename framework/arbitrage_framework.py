import time
import logging
from framework.exchange_manager import ExchangeManager
from framework.arbitrage_opportunity import ArbitrageOpportunity
from config.config import DISABLE_TRADES, ARBITRAGE_PERCENT

# Initialize logger
logger = logging.getLogger('ArbitrageBot')

class ArbitrageFramework:
    """
    ArbitrageFramework class to manage the overall arbitrage trading strategy across multiple exchanges.

    This class coordinates the fetching of prices, checking for arbitrage opportunities, managing accounts,
    and executing trades.
    """

    def __init__(self, exchanges):
        """
        Initialize the ArbitrageFramework with exchange information.

        Parameters:
        - exchanges (dict): A dictionary of exchange names mapped to ccxt exchange objects.

        Attributes:
        - exchange_manager (ExchangeManager): Manages the fetching of price data from exchanges.
        """
        logger.debug("Initializing ArbitrageFramework.")

        # Store the exchanges in the class attribute
        self.exchanges = exchanges  # Initialize the exchanges attribute here
        self.exchange_manager = ExchangeManager(exchanges)

        # Fetch and log balances for each exchange and currency if logging level is set to DEBUG
        for exchange_name in self.exchanges:
            try:
                balance = self.exchanges[exchange_name].fetch_balance()
                logger.info(f"Balances on {exchange_name}:")
                for currency, balance_data in balance['free'].items():
                    if balance_data > 0:  # Only log currencies with a balance greater than zero
                        logger.info(f"  {currency}: {balance_data}")
            except Exception as e:
                logger.error(f"Failed to fetch balances for {exchange_name}: {e}")

    def send_email(subject, body):
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
    
        gmail_user = EMAIL['sender']
        gmail_password = EMAIL['sender_token']
        to_email = EMAIL['recipient']
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
    
        msg.attach(MIMEText(body, 'plain'))
    
        try:
            logger.debug("Attempting to send email.")
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_password)
            text = msg.as_string()
            server.sendmail(gmail_user, to_email, text)
            server.quit()
            logger.info("Email sent successfully")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

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
                    arbitrage_opportunity = ArbitrageOpportunity()
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
        # Filter opportunities that are greater than ARBITRAGE_PERCENT
        viable_opportunities = [
            opportunity for opportunity in opportunities
            if opportunity['gross_profit_percentage'] > ARBITRAGE_PERCENT
        ]
    
        # Sort viable opportunities by gross profit percentage in descending order
        viable_opportunities.sort(key=lambda x: x['gross_profit_percentage'], reverse=True)
    
        if viable_opportunities:
            logger.info(f"Arbitrage opportunities greater than {ARBITRAGE_PERCENT}% found.")
    
            if DISABLE_TRADES:
                # Log each opportunity when trades are disabled
                for opportunity in viable_opportunities:
                    logger.info(f"Arbitrage Opportunity: {opportunity['gross_profit_percentage']:.2f}%")
                    logger.info(f"  Buy {opportunity['buy_pair']} on {opportunity['buy_exchange']} at "
                                f"{opportunity['buy_price']:.10f}")
                    logger.info(f"  Sell {opportunity['sell_pair']} on {opportunity['sell_exchange']} at "
                                f"{opportunity['sell_price']:.10f}")
                    logger.info(f"  Estimated Profit: {opportunity['gross_profit_percentage']:.2f}%")
    
            # Proceed to execute the best opportunity if trades are enabled
            if not DISABLE_TRADES:
                for opportunity in viable_opportunities:
                    success = self.execute_trade(opportunity)
                    if success:
                        # Send email notification about the executed trade
                        subject = "Arbitrage Trade Executed"
                        body = (f"Trade executed successfully:\n"
                                f"Buy {opportunity['buy_pair']} on {opportunity['buy_exchange']} at "
                                f"{opportunity['buy_price']:.10f}\n"
                                f"Sell {opportunity['sell_pair']} on {opportunity['sell_exchange']} at "
                                f"{opportunity['sell_price']:.10f}\n"
                                f"Trade Amount: {min(opportunity['buy_amount'], opportunity['sell_amount'])}")
                        self.send_email(subject, body)
                        logger.info("Arbitrage opportunity executed successfully.")
                        break  # Exit the loop after a successful trade
                    else:
                        logger.info("Moving to the next viable opportunity due to insufficient funds.")
        else:
            logger.debug("No viable arbitrage opportunities found above the threshold or exchange is on cooldown.")

    def execute_trade(self, opportunity):
        """
        Execute the trade for a given arbitrage opportunity.
    
        This method performs the trade, logging the details and updating account balances accordingly.
    
        Parameters:
        - opportunity (dict): A dictionary representing the arbitrage opportunity.
    
        Returns:
        - bool: True if the trade was successful, False otherwise.
        """
        logger.info("Arbitrage Opportunity Found:")
        logger.info(f"Buy {opportunity['buy_pair']} on {opportunity['buy_exchange']} at {opportunity['buy_price']:.10f}")
        logger.info(f"Sell {opportunity['sell_pair']} on {opportunity['sell_exchange']} at {opportunity['sell_price']:.10f}")
    
        # Check balances
        buy_currency = opportunity['buy_pair'].split('/')[0]
        sell_currency = opportunity['sell_pair'].split('/')[0]
    
        buy_balance = self.get_balance(opportunity['buy_exchange'], buy_currency)
        sell_balance = self.get_balance(opportunity['sell_exchange'], sell_currency)
    
        # Define minimum balance requirements
        min_balances = {
            'ETH': 0.15,
            'LTC': 5,
            'BTC': 0.0075
        }
    
        # Check if both the buy and sell currencies meet the minimum balance requirements
        if buy_balance >= min_balances.get(buy_currency, 0) and sell_balance >= min_balances.get(sell_currency, 0):
            # Proceed with executing the trade
            logger.info("Sufficient balances found. Executing trade.")
    
            try:
                # Trade the minimum amount of the two currencies
                trade_amount = min(buy_balance, sell_balance)
    
                # Execute buy order
                buy_order = self.exchanges[opportunity['buy_exchange']].create_order(
                    symbol=opportunity['buy_pair'],
                    type='market',
                    side='buy',
                    amount=trade_amount
                )
                logger.info(f"Buy order executed: {buy_order}")
    
                # Execute sell order
                sell_order = self.exchanges[opportunity['sell_exchange']].create_order(
                    symbol=opportunity['sell_pair'],
                    type='market',
                    side='sell',
                    amount=trade_amount
                )
                logger.info(f"Sell order executed: {sell_order}")
    
                # Update cooldown tracker (Implement the logic as needed)
                # self.cooldown_tracker[opportunity['buy_exchange']] = time.time() + 3600  # 1-hour cooldown
    
                # Fetch and log balances for each exchange and currency if logging level is set to DEBUG
                for exchange_name in self.exchanges:
                    try:
                        balance = self.exchanges[exchange_name].fetch_balance()
                        logger.info(f"Balances on {exchange_name}:")
                        for currency, balance_data in balance['free'].items():
                            if balance_data > 0:  # Only log currencies with a balance greater than zero
                                logger.info(f"  {currency}: {balance_data}")
                    except Exception as e:
                        logger.error(f"Failed to fetch balances for {exchange_name}: {e}")
                
                return True
            except Exception as e:
                logger.error(f"Trade execution failed: {e}")
                return False
        else:
            logger.info("Insufficient balance for trade execution.")
            return False

    def get_balance(self, exchange_name, currency):
        """
        Retrieve the balance for a given currency on a specific exchange.

        Parameters:
        - exchange_name (str): The name of the exchange.
        - currency (str): The currency for which to retrieve the balance.

        Returns:
        - float: The available balance for the currency.
        """
        try:
            balance = self.exchanges[exchange_name].fetch_balance()
            available_balance = balance['free'][currency]
            logger.debug(f"Balance for {currency} on {exchange_name}: {available_balance}")
            return available_balance
        except Exception as e:
            logger.error(f"Failed to fetch balance for {currency} on {exchange_name}: {e}")
            return 0
