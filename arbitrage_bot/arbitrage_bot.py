import ccxt
import time
import csv
import os
import logging
import socket
from dotenv import load_dotenv
from framework.arbitrage_framework import ArbitrageFramework
from config.config import EXCHANGES, LOGGING_CONFIG

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

def send_email(subject, body):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    gmail_user = 'mike.fuscoletti@gmail.com'
    gmail_password = 'goxje6-bufdYg-zikdix'
    to_email = 'mike.fuscoletti@gmail.com'

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

def initialize_exchanges():
    """Initialize exchanges based on the configuration file."""
    exchange_objects = {}
    for name, config in EXCHANGES.items():
        logger.debug(f"Initializing exchange: {name}")
        exchange_class = getattr(ccxt, config['class'])
        exchange_objects[name] = exchange_class({
            'apiKey': config['apiKey'],
            'secret': config['secret'],
        })
    logger.info(f"Exchanges initialized: {list(exchange_objects.keys())}")
    return exchange_objects

def real_time_arbitrage_bot():
    logger.info("Starting real-time arbitrage bot.")
    exchanges = initialize_exchanges()
    framework = ArbitrageFramework(initial_account_value=10000, exchanges=exchanges)

    # Create CSV file if it doesn't exist
    if not os.path.isfile('opportunities.csv'):
        logger.debug("Creating opportunities CSV file.")
        with open('opportunities.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Buy Exchange", "Sell Exchange", "Buy Pair", "Sell Pair", "Buy Price", "Sell Price", "Gross Profit (%)", "Net Profit", "Total Taxes", "Total Fees", "Total Money Out"])

    last_log_time = time.time()
    while True:
        logger.debug("Fetching real-time prices.")
        prices = framework.exchange_manager.get_real_time_prices()  # No need to pass exchanges
        logger.debug(f"Prices fetched: {prices}")

        logger.debug("Checking for arbitrage opportunities.")
        opportunities = framework.check_real_time_arbitrage(prices)  # Get the list of opportunities

        if opportunities:
            framework.execute_best_opportunity(opportunities)  # Execute the best opportunity

        # Log activity every hour
        current_time = time.time()
        if current_time - last_log_time >= 900:  # Log every 15 minutes for demonstration, can be changed
            logger.info("Still running. Last prices found:")
            for exchange, pairs in prices.items():
                logger.info(f"{exchange}: {pairs}")
            last_log_time = current_time
        
        logger.debug("Sleeping for 30 seconds before the next check.")
        time.sleep(15)  # Check every 30 seconds

# Start the bot
real_time_arbitrage_bot()
