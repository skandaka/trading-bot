import yfinance as yf
import os
import time
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'JPM', 'BAC', 'WFC',
    'GS', 'MS', 'C', 'UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'TMO', 'WMT',
    'PG', 'KO', 'PEP', 'COST', 'NKE', 'BA', 'CAT', 'GE', 'MMM', 'UPS', 'RTX'
]

CACHE_DIR = "local_data_cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def download_all_data():
    logger.info(f"Starting one-time data download for {len(STOCKS)} stocks...")
    for symbol in STOCKS:
        try:
            logger.info(f"Downloading data for {symbol}...")
            data = yf.download(symbol, period="2y", interval="1d", progress=False)

            if data.empty:
                logger.warning(f"No data found for {symbol}. Skipping.")
                continue

            file_path = os.path.join(CACHE_DIR, f"{symbol}.csv")
            data.to_csv(file_path)

            logger.info(f"✓ Saved {len(data)} rows for {symbol} to {file_path}")
            # Be very respectful to the API to avoid getting blocked
            time.sleep(10)

        except Exception as e:
            logger.error(f"Could not download data for {symbol}: {e}")

    logger.info("\n" + "=" * 50)
    logger.info("LOCAL DATA CACHE CREATION COMPLETE!")
    logger.info("You can now run the main data pipeline.")
    logger.info("=" * 50)


if __name__ == "__main__":
    download_all_data()