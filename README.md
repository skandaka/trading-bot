# AI Trading Bot

An algorithmic trading bot that uses machine learning to predict stock movements.

## Setup
1. Open in PyCharm Professional
2. PyCharm will detect and use the virtual environment
3. Copy `.env.example` to `.env` and add your API keys
4. Run `market_data.py` to test connection

## Architecture
- Data Collection: Fetches market data from Alpaca
- ML Models: LSTM neural networks for prediction
- Trading Engine: Executes trades via Alpaca paper trading
- Dashboard: React-based monitoring interface