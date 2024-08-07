# config.py

import os
from dotenv import load_dotenv

load_dotenv()

ARBITRAGE_PERCENT = 1.35

# Disable Live Trading
DISABLE_TRADES = True
TEST_HOURS = 10

# Logging configuration
LOGGING_CONFIG = {
    'level': 'DEBUG',  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    'file': 'arbitrage_bot.log',
    'console': True
}

CRYPTOS = ['BTC', 'ETH', 'LTC', 'XRP', 'BCH', 'ADA', 'DOT', 'BNB', 'SOL', 'LINK', 'XLM', 'UNI', 'MATIC', 'DOGE', 'AVAX', 'VET', 'TRX', 'XTZ']

# Exchange configuration with environment variables for sensitive data
EXCHANGES = {
    'kraken': {
        'class': 'kraken',
        'apiKey': os.getenv('KRAKEN_API_KEY', 'default_api_key'),  # Fallback for local testing
        'secret': os.getenv('KRAKEN_SECRET', 'default_secret'),    # Fallback for local testing
    },
    'binance': {
        'class': 'binanceus',
        'apiKey': os.getenv('BINANCE_API_KEY', 'default_api_key'),  # Fallback for local testing
        'secret': os.getenv('BINANCE_SECRET', 'default_secret'),    # Fallback for local testing
    }
}

EMAIL = {
    'sender': 'mike.fuscoletti@gmail.com',
    'sender_token': os.getenv('GMAIL_TOKEN', 'default_api_key'),
    'recipient': 'mike.fuscoletti@gmail.com'
}
