name: Run Arbitrage Bot

on:
  workflow_dispatch:

jobs:
  run-bot:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x' # Automatically picks the latest Python 3.x version

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run Arbitrage Bot
      env:
        KRAKEN_API_KEY: ${{ secrets.KRAKEN_API_KEY }}
        KRAKEN_SECRET: ${{ secrets.KRAKEN_SECRET }}
        BINANCE_API_KEY: ${{ secrets.BINANCE_API_KEY }}
        BINANCE_SECRET: ${{ secrets.BINANCE_SECRET }}
      run: |
        python -m arbitrage_bot.arbitrage_bot
