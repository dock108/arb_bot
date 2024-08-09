import ccxt
import logging
from config.config import CRYPTOS

# Initialize logger
logger = logging.getLogger('ArbitrageBot')

class ExchangeManager:
    """
    ExchangeManager class to handle interactions with cryptocurrency exchanges.

    This class manages the fetching of market data, including real-time prices
    for fiat and crypto-to-crypto pairs across multiple exchanges, as well as logging balances.
    """

    def __init__(self, exchanges):
        """
        Initialize the ExchangeManager.

        Parameters:
        - exchanges (dict): A dictionary of exchange names mapped to ccxt exchange objects.
        """
        logger.debug("Initializing ExchangeManager.")
        self.exchanges = exchanges

    def log_exchange_balances(self):
        """Log the balances of each exchange."""
        for exchange_name in self.exchanges:
            try:
                balance = self.exchanges[exchange_name].fetch_balance()
                logger.info(f"Balances on {exchange_name}:")
                for currency, balance_data in balance['free'].items():
                    if balance_data > 0:
                        logger.info(f"  {currency}: {balance_data}")
            except Exception as e:
                logger.error(f"Failed to fetch balances for {exchange_name}: {e}")

    def load_markets(self, exchange_name, exchange):
        """
        Load market data for the given exchange.

        Parameters:
        - exchange_name (str): The name of the exchange.
        - exchange (ccxt.Exchange): The ccxt exchange object.

        Returns:
        - dict: A dictionary of available markets on the exchange.
        """
        try:
            markets = exchange.load_markets()
            logger.debug(f"Loaded markets for {exchange_name}.")
            return markets
        except ccxt.BaseError as e:
            logger.error(f"Error loading markets for {exchange_name}: {str(e)}")
            return {}

    def fetch_pair_prices(self, exchange_name, exchange, markets, pair):
        """
        Fetch the bid, ask, and last prices for a given trading pair on an exchange.

        Parameters:
        - exchange_name (str): The name of the exchange.
        - exchange (ccxt.Exchange): The ccxt exchange object.
        - markets (dict): A dictionary of available markets on the exchange.
        - pair (str): The trading pair to fetch the prices for.

        Returns:
        - dict: A dictionary containing the bid, ask, and last prices for the trading pair,
                or an empty dictionary if the prices are not available.
        """
        if not self.is_pair_available(markets, pair):
            logger.debug(f"Market symbol {pair} not available on {exchange_name}")
            return {}

        try:
            ticker = exchange.fetch_ticker(pair)
            return self.extract_prices_from_ticker(ticker, exchange_name, pair)
        except ccxt.BaseError as e:
            logger.error(f"Error fetching {pair} from {exchange_name}: {str(e)}")
            return {}

    def is_pair_available(self, markets, pair):
        """
        Check if the trading pair is available in the exchange's markets.

        Parameters:
        - markets (dict): A dictionary of available markets on the exchange.
        - pair (str): The trading pair.

        Returns:
        - bool: True if the pair is available, otherwise False.
        """
        return pair in markets

    def extract_prices_from_ticker(self, ticker, exchange_name, pair):
        """
        Extract the bid, ask, and last prices from the ticker information.

        Parameters:
        - ticker (dict): The ticker data returned by the exchange.
        - exchange_name (str): The name of the exchange.
        - pair (str): The trading pair.

        Returns:
        - dict: A dictionary containing the bid, ask, and last prices for the trading pair.
        """
        bid_price = ticker.get('bid')
        ask_price = ticker.get('ask')
        last_price = ticker.get('last')

        if bid_price is None or ask_price is None:
            logger.debug(f"No bid/ask price for {pair} on {exchange_name}")
            return {}

        logger.debug(f"Fetched {pair} prices from {exchange_name}: Bid: {bid_price}, Ask: {ask_price}, Last: {last_price}")

        # Construct the result dictionary, handling None values for last_price
        result = {
            'bid': float(bid_price),
            'ask': float(ask_price)
        }
        if last_price is not None:
            result['last'] = float(last_price)

        return result

    def get_real_time_prices(self):
        """
        Fetch real-time prices for all relevant crypto pairs with BTC or ETH as the denominators
        from configured exchanges.

        Returns:
        - dict: A dictionary containing price data for each exchange.
        """
        logger.debug("Fetching real-time prices.")
        prices = {}
        denominators = ["BTC", "ETH"]

        for exchange_name, exchange in self.exchanges.items():
            exchange_prices = self.fetch_exchange_prices(exchange_name, exchange, denominators)
            if exchange_prices:  # Ensure exchange_prices is not empty
                prices[exchange_name] = exchange_prices

        logger.debug(f"Fetched prices: {prices}")
        return prices

    def fetch_exchange_prices(self, exchange_name, exchange, denominators):
        """
        Fetch prices for an individual exchange, filtering for pairs with specified denominators.

        Parameters:
        - exchange_name (str): The name of the exchange.
        - exchange (object): The exchange object.
        - denominators (list): List of denominators to filter pairs (e.g., ["BTC", "ETH"]).

        Returns:
        - dict: A dictionary containing the price data for the exchange.
        """
        exchange_prices = {}
        markets = self.load_markets(exchange_name, exchange)

        for crypto in CRYPTOS:
            for denominator in denominators:
                pair = f"{crypto}/{denominator}"
                pair_prices = self.fetch_and_validate_pair_prices(exchange_name, exchange, markets, pair)
                if pair_prices:
                    exchange_prices[pair] = pair_prices

        return exchange_prices

    def fetch_and_validate_pair_prices(self, exchange_name, exchange, markets, pair):
        """
        Fetch and validate the prices for a specific trading pair.

        Parameters:
        - exchange_name (str): The name of the exchange.
        - exchange (object): The exchange object.
        - markets (dict): Dictionary of available markets on the exchange.
        - pair (str): The trading pair (e.g., "BTC/ETH").

        Returns:
        - dict or None: The prices for the trading pair if valid, otherwise None.
        """
        if pair in markets:
            pair_prices = self.fetch_pair_prices(exchange_name, exchange, markets, pair)
            if pair_prices:
                return pair_prices
        return None
