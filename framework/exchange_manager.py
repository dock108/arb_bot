import ccxt
import logging
from config.config import CRYPTOS

# Initialize logger
logger = logging.getLogger('ArbitrageBot')

class ExchangeManager:
    """
    ExchangeManager class to handle interactions with cryptocurrency exchanges.

    This class manages the fetching of market data, including real-time prices
    for fiat and crypto-to-crypto pairs across multiple exchanges.
    """

    def __init__(self, exchanges):
        """
        Initialize the ExchangeManager.

        Parameters:
        - exchanges (dict): A dictionary of exchange names mapped to ccxt exchange objects.
        """
        logger.debug("Initializing ExchangeManager.")
        self.exchanges = exchanges

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

        This method attempts to retrieve the latest prices for the specified trading pair,
        logging any issues encountered during the process.

        Parameters:
        - exchange_name (str): The name of the exchange.
        - exchange (ccxt.Exchange): The ccxt exchange object.
        - markets (dict): A dictionary of available markets on the exchange.
        - pair (str): The trading pair to fetch the prices for.

        Returns:
        - dict: A dictionary containing the bid, ask, and last prices for the trading pair,
                or an empty dictionary if the prices are not available.
        """
        if pair in markets:
            try:
                ticker = exchange.fetch_ticker(pair)
                bid_price = ticker.get('bid', None)
                ask_price = ticker.get('ask', None)
                last_price = ticker.get('last', None)

                if bid_price is not None and ask_price is not None:
                    logger.debug(f"Fetched {pair} prices from {exchange_name}: Bid: {bid_price}, Ask: {ask_price}, Last: {last_price}")
                    return {
                        'bid': float(bid_price),
                        'ask': float(ask_price),
                        'last': float(last_price)
                    }
                else:
                    logger.debug(f"No bid/ask price for {pair} on {exchange_name}")
            except ccxt.BaseError as e:
                logger.error(f"Error fetching {pair} from {exchange_name}: {str(e)}")
        else:
            logger.debug(f"Market symbol {pair} not available on {exchange_name}")
        
        return {}  # Return an empty dictionary if prices are not available

    def get_real_time_prices(self):
        """
        Fetch real-time prices for all relevant crypto and fiat pairs from configured exchanges.

        This method retrieves the latest price data for fiat pairs and crypto-to-crypto pairs,
        handling the differences in available market symbols across exchanges.

        Returns:
        - dict: A dictionary containing price data for each exchange.
        """
        logger.debug("Fetching real-time prices.")
        prices = {}
        
        for exchange_name, exchange in self.exchanges.items():
            exchange_prices = {}
            markets = self.load_markets(exchange_name, exchange)

            # Fetch crypto-to-crypto pairs
            for i, crypto1 in enumerate(CRYPTOS):
                for crypto2 in CRYPTOS[i + 1:]:
                    pair = f"{crypto1}/{crypto2}"
                    pair_prices = self.fetch_pair_prices(exchange_name, exchange, markets, pair)
                    
                    # Try reverse pair if necessary
                    if not pair_prices:
                        reverse_pair = f"{crypto2}/{crypto1}"
                        pair_prices = self.fetch_pair_prices(exchange_name, exchange, markets, reverse_pair)

                    if pair_prices:  # Ensure pair_prices is not empty
                        exchange_prices[pair] = pair_prices

            prices[exchange_name] = exchange_prices
        logger.debug(f"Fetched prices: {prices}")
        return prices
