import ccxt
import time
import logging
import socket
from dotenv import load_dotenv
from framework.arbitrage_framework import ArbitrageFramework
from config.config import LOGGING_CONFIG, EXCHANGES, DISABLE_TRADES, TEST_HOURS

load_dotenv()

# Configure logging
def setup_logging():
    """
    Set up logging based on the configuration file.
    
    Returns:
    - logger (logging.Logger): Configured logger instance.
    """
    logging_level = getattr(logging, LOGGING_CONFIG['level'].upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger('ArbitrageBot')
    logger.setLevel(logging_level)
    
    # Create file handler
    file_handler = logging.FileHandler(LOGGING_CONFIG['file'])
    file_handler.setLevel(logging_level)
    
    # Create console handler
    if LOGGING_CONFIG['console']:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging_level)
        logger.addHandler(console_handler)
    
    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    if LOGGING_CONFIG['console']:
        console_handler.setFormatter(formatter)
    
    # Add the file handler to the logger
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# Force Python to use IPv4 for all outgoing connections
def force_ipv4():
    """
    Force the bot to use IPv4 for all outgoing connections by overriding the default socket behavior.
    """
    logger.debug("Forcing IPv4 usage for all outgoing connections.")
    original_getaddrinfo = socket.getaddrinfo

    def getaddrinfo_ipv4(*args, **kwargs):
        # Only request IPv4 addresses
        return [
            info for info in original_getaddrinfo(*args, **kwargs)
            if info[0] == socket.AF_INET
        ]

    socket.getaddrinfo = getaddrinfo_ipv4

force_ipv4()

def initialize_exchanges():
    """
    Initialize exchange connections based on the configuration file.
    
    Returns:
    - exchange_objects (dict): Dictionary of initialized exchange objects.
    """
    exchange_objects = {}
    for name, config in EXCHANGES.items():
        logger.debug(f"Initializing exchange: {name}")
        logger.debug(f"Exchange class: {config['class']}")

        try:
            exchange_class = getattr(ccxt, config['class'])
            exchange_objects[name] = exchange_class({
                'apiKey': config['apiKey'],
                'secret': config['secret'],
            })
            markets = exchange_objects[name].load_markets()
            logger.debug(f"Successfully connected to {name}. Markets loaded: {list(markets.keys())[:5]}...")
        except AttributeError as e:
            logger.error(f"Exchange class '{config['class']}' not found in ccxt for {name}: {e}")
        except ccxt.AuthenticationError as e:
            logger.error(f"Authentication error with {name}: {e}")
        except Exception as e:
            logger.error(f"Error initializing {name}: {e}")

    logger.info(f"Exchanges initialized: {list(exchange_objects.keys())}")
    return exchange_objects

def real_time_arbitrage_bot():
    """
    Main loop for the real-time arbitrage bot.
    Initializes exchanges, fetches prices, finds opportunities, executes trades, and logs activity.
    """
    logger.info("Starting real-time arbitrage bot.")
    exchanges = initialize_exchanges()
    framework = ArbitrageFramework(exchanges=exchanges)

    start_time = time.time()
    last_log_time = start_time

    while True:
        prices = fetch_prices(framework)
        opportunities = find_arbitrage_opportunities(framework, prices)

        if opportunities:
            execute_best_opportunity(framework, opportunities)

        last_log_time = log_activity_if_needed(prices, last_log_time)

        if should_stop_bot(start_time):
            logger.info("Shutting down the bot.")
            break

        sleep_before_next_check()

def fetch_prices(framework):
    """
    Fetch real-time prices from the exchanges using the arbitrage framework.

    Parameters:
    - framework (ArbitrageFramework): The arbitrage framework instance.

    Returns:
    - prices (dict): Dictionary containing the fetched prices from all exchanges.
    """
    logger.debug("Fetching real-time prices.")
    prices = framework.exchange_manager.get_real_time_prices()
    logger.debug(f"Prices fetched: {prices}")
    return prices

def find_arbitrage_opportunities(framework, prices):
    """
    Check for and return arbitrage opportunities based on the fetched prices.

    Parameters:
    - framework (ArbitrageFramework): The arbitrage framework instance.
    - prices (dict): Dictionary of current prices from exchanges.

    Returns:
    - opportunities (list): List of potential arbitrage opportunities.
    """
    logger.debug("Checking for arbitrage opportunities.")
    opportunities = framework.check_real_time_arbitrage(prices)
    return opportunities

def execute_best_opportunity(framework, opportunities):
    """
    Execute the best arbitrage opportunity found.

    Parameters:
    - framework (ArbitrageFramework): The arbitrage framework instance.
    - opportunities (list): List of potential arbitrage opportunities.
    """
    framework.execute_best_opportunity(opportunities)

def log_activity_if_needed(prices, last_log_time):
    """
    Log bot activity if the logging interval has passed.

    Parameters:
    - prices (dict): Dictionary of current prices from exchanges.
    - last_log_time (float): The last time activity was logged.

    Returns:
    - last_log_time (float): Updated last log time.
    """
    log_interval = LOGGING_CONFIG['log_minutes'] * 60
    current_time = time.time()
    if current_time - last_log_time >= log_interval:
        logger.info("Still running. Last prices found:")
        for exchange, pairs in prices.items():
            logger.info(f"{exchange}: {pairs}")
        return current_time
    return last_log_time

def should_stop_bot(start_time):
    """
    Check if the bot should stop based on the configured test duration.

    Parameters:
    - start_time (float): The time when the bot started.

    Returns:
    - bool: True if the bot should stop, False otherwise.
    """
    if DISABLE_TRADES:
        elapsed_hours = (time.time() - start_time) / 3600
        if elapsed_hours >= TEST_HOURS:
            logger.info(f"Test duration of {TEST_HOURS} hours completed.")
            return True
    return False

def sleep_before_next_check():
    """
    Pause the bot for a fixed interval before the next check.
    """
    logger.debug("Sleeping for 30 seconds before the next check.")
    time.sleep(30)

# Start the bot
real_time_arbitrage_bot()
