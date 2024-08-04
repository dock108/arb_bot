import logging

# Initialize logger
logger = logging.getLogger('ArbitrageBot')

class ProfitCalculator:
    """
    ProfitCalculator class to handle the calculation of gross and net profits for trades.

    This class calculates potential profits from trades, including gross and net profits,
    and accounts for trading fees and taxes.
    """

    def __init__(self, average_fee=0.002867, tax_rate=0.275):
        """
        Initialize the ProfitCalculator with the specified average trading fee and tax rate.

        Parameters:
        - average_fee (float): The average trading fee percentage for transactions.
        - tax_rate (float): The tax rate applied to gross profits for calculating net profit.
        """
        self.average_fee = average_fee
        self.tax_rate = tax_rate
        self.tax_tally = 0
        self.fees_tally = 0

    
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
    
    def calculate_net_profit(self, gross_profit, trade_value):
        """
        Calculate the net profit after fees and taxes for a given trade.

        This method accounts for trading fees on both the buy and sell transactions, as well as
        short-term capital gains taxes on the gross profit. It updates the tallies for fees and taxes.

        Parameters:
        - gross_profit (float): The gross profit before any deductions.
        - trade_value (float): The value of the trade (amount involved in the transaction).

        Returns:
        - net_profit (float): The net profit after deducting fees and taxes.
        - fees (float): The total fees deducted for the trade.
        - taxes (float): The total taxes deducted based on the gross profit.
        """
        logger.debug(f"Calculating net profit for gross profit: {gross_profit}, trade value: {trade_value}")
        fees = trade_value * self.average_fee * 2  # Calculate fees for both buying and selling
        taxes = gross_profit * 0.275  # Calculate taxes as 27.5% of gross profit
        net_profit = gross_profit - fees - taxes  # Net profit after fees and taxes
        self.tax_tally += taxes  # Update tax tally
        self.fees_tally += fees  # Update fees tally
        logger.info(f"Calculated net profit: {net_profit}, Fees: {fees}, Taxes: {taxes}")
        return net_profit, fees, taxes
    
    def get_tax_tally(self):
        """
        Retrieve the accumulated tax tally.

        Returns:
        - float: The total taxes tallied so far.
        """
        return self.tax_tally

    def get_fees_tally(self):
        """
        Retrieve the accumulated fees tally.

        Returns:
        - float: The total fees tallied so far.
        """
        return self.fees_tally
