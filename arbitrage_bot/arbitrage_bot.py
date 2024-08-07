import ccxt
import time
import logging
import socket
from dotenv import load_dotenv
from framework.arbitrage_framework import ArbitrageFramework
from config.config import LOGGING_CONFIG, EXCHANGES, EMAIL, DISABLE_TRADES, TEST_HOURS

load_dotenv()

# Configure logging
def setup_logging():
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
    """Initialize exchanges based on the configuration file."""
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
    logger.info("Starting real-time arbitrage bot.")
    exchanges = initialize_exchanges()
    framework = ArbitrageFramework(exchanges=exchanges)

    start_time = time.time()
    last_log_time = start_time

    while True:
        logger.debug("Fetching real-time prices.")
        prices = framework.exchange_manager.get_real_time_prices()
        logger.debug(f"Prices fetched: {prices}")

        logger.debug("Checking for arbitrage opportunities.")
        opportunities = framework.check_real_time_arbitrage(prices)  # Get the list of opportunities

        if opportunities:
            framework.execute_best_opportunity(opportunities)  # Execute the best opportunity

        # Log activity every hour
        current_time = time.time()
        if current_time - last_log_time >= 3600:
            logger.info("Still running. Last prices found:")
            for exchange, pairs in prices.items():
                logger.info(f"{exchange}: {pairs}")
            last_log_time = current_time

        # Check if the test duration has elapsed if trades are disabled
        if DISABLE_TRADES:
            elapsed_hours = (current_time - start_time) / 3600
            if elapsed_hours >= TEST_HOURS:
                logger.info(f"Test duration of {TEST_HOURS} hours completed. Shutting down.")
                break  # Exit the loop to stop the bot
        
        logger.debug("Sleeping for 30 seconds before the next check.")
        time.sleep(30)  # Check every 30 seconds

# Start the bot
real_time_arbitrage_bot()
