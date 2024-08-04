# config.py

import os

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

CRYPTOS = ['BTC', 'LTC', 'ETH']
FIAT = 'USD'

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    'file': 'arbitrage_bot.log',
    'console': True
}