import logging
from framework.exchange_manager import ExchangeManager
from framework.arbitrage_opportunity import ArbitrageOpportunity
from config.config import DISABLE_TRADES, ARBITRAGE_PERCENT, EMAIL

# Initialize logger
logger = logging.getLogger('ArbitrageBot')

class ArbitrageFramework:
    """
    ArbitrageFramework class to manage the overall arbitrage trading strategy across multiple exchanges.
    """

    def __init__(self, exchanges):
        """
        Initialize the ArbitrageFramework with exchange information.
        """
        logger.debug("Initializing ArbitrageFramework.")

        self.exchange_manager = ExchangeManager(exchanges)
        self.arbitrage_opportunity = ArbitrageOpportunity()

        # Log balances for each exchange using the ExchangeManager
        self.exchange_manager.log_exchange_balances()

    def send_email(self, subject, body):
        """Send an email notification."""
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
        Check for real-time arbitrage opportunities.

        Parameters:
        - prices (dict): A dictionary containing the latest price data for various pairs across exchanges.

        Returns:
        - list: A list of arbitrage opportunities found.
        """
        logger.debug("Checking for real-time arbitrage opportunities.")
        opportunities = []

        for buy_exchange in prices:
            for sell_exchange in prices:
                if buy_exchange != sell_exchange:
                    opportunities.extend(
                        self.arbitrage_opportunity.find_arbitrage_opportunities(
                            prices, buy_exchange, sell_exchange
                        )
                    )

        return opportunities
    
    def execute_best_opportunity(self, opportunities):
        """
        Evaluate and execute the best arbitrage opportunity if viable.
        """
        viable_opportunities = self.filter_viable_opportunities(opportunities)

        if viable_opportunities:
            logger.info(f"Arbitrage opportunities greater than {ARBITRAGE_PERCENT}% found.")
            self.log_opportunities(viable_opportunities)

            if not DISABLE_TRADES:
                self.execute_trade_on_best_opportunity(viable_opportunities)
        else:
            logger.debug("No viable arbitrage opportunities found.")

    def filter_viable_opportunities(self, opportunities):
        """
        Filter opportunities to find those that are viable based on the arbitrage percentage.

        Parameters:
        - opportunities (list): List of arbitrage opportunities.

        Returns:
        - list: A list of viable opportunities sorted by gross profit percentage.
        """
        viable_opportunities = [
            opportunity for opportunity in opportunities
            if self.arbitrage_opportunity.calculate_gross_profit(opportunity['buy_price'], opportunity['sell_price']) > ARBITRAGE_PERCENT
        ]
        viable_opportunities.sort(key=lambda x: x['gross_profit_percentage'], reverse=True)
        return viable_opportunities

    def log_opportunities(self, opportunities):
        """
        Log the viable arbitrage opportunities.

        Parameters:
        - opportunities (list): List of viable arbitrage opportunities.
        """
        if DISABLE_TRADES:
            for opportunity in opportunities:
                logger.info(f"Arbitrage Opportunity: {opportunity['gross_profit_percentage']:.2f}%")
                logger.info(f"  Buy {opportunity['buy_pair']} on {opportunity['buy_exchange']} at ask price: {opportunity['buy_price']:.10f}")
                logger.info(f"  Sell {opportunity['sell_pair']} on {opportunity['sell_exchange']} at bid price: {opportunity['sell_price']:.10f}")

    def execute_trade_on_best_opportunity(self, opportunities):
        """
        Execute the trade for the best arbitrage opportunity.

        Parameters:
        - opportunities (list): List of viable arbitrage opportunities.
        """
        for opportunity in opportunities:
            success = self.arbitrage_opportunity.execute_trade(opportunity, self.exchange_manager.exchanges)
            if success:
                self.notify_trade_success(opportunity)
                break

    def notify_trade_success(self, opportunity):
        """
        Send a notification for a successful trade execution.

        Parameters:
        - opportunity (dict): The arbitrage opportunity that was executed.
        """
        subject = "Arbitrage Trade Executed"
        body = (
            f"Trade executed successfully:\n"
            f"Buy {opportunity['buy_pair']} on {opportunity['buy_exchange']} at ask price: {opportunity['buy_price']:.10f}\n"
            f"Sell {opportunity['sell_pair']} on {opportunity['sell_exchange']} at bid price: {opportunity['sell_price']:.10f}\n"
            f"Trade Amount: {min(opportunity['buy_amount'], opportunity['sell_amount'])}"
        )
        self.send_email(subject, body)
