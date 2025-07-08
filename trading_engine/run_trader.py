import os
import sys
import logging
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_engine.engine import TradingEngine

load_dotenv()


def main():
    stocks_to_trade = ['AAPL', 'MSFT', 'GOOGL', 'JPM']

    logging.info("--- 🤖 Starting Trading Bot ---")

    for symbol in stocks_to_trade:
        try:
            engine = TradingEngine(symbol)
            engine.run()
        except Exception as e:
            logging.error(f"An error occurred in the engine for {symbol}: {e}", exc_info=True)

    logging.info("--- ✅ Trading Bot session complete ---")


if __name__ == "__main__":
    main()