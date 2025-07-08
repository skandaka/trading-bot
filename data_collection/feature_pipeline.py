import os
import sys
import logging
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from io import BytesIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection.azure_data_manager import AzureDataManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FeaturePipeline:
    def __init__(self, use_azure=True):
        self.use_azure = use_azure
        if self.use_azure:
            self.azure_manager = AzureDataManager(container_name="features")
            self.azure_manager.create_container_if_not_exists()

    def run_pipeline(self, symbol: str):
        logger.info(f"🚀 Starting feature pipeline for {symbol}...")

        df = self.download_market_data(symbol)
        if df is None or df.empty:
            return

        df_features = self.create_features(df.copy())

        self.save_features(df_features, symbol)
        logger.info(f"✅ Successfully completed feature pipeline for {symbol}.")

    def download_market_data(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        logger.info(f"Downloading {period} of historical data for {symbol}...")
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period=period, auto_adjust=True)
            if df.empty:
                logger.warning(f"No data returned from yfinance for {symbol}")
                return None
            df.rename(columns={"Close": "close", "High": "high", "Low": "low", "Open": "open", "Volume": "volume"},
                      inplace=True)
            logger.info(f"Downloaded {df.shape[0]} data points.")
            return df
        except Exception as e:
            logger.error(f"Failed to download data for {symbol}: {e}")
            return None

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        logger.info("Calculating technical indicators...")

        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.ema(length=20, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(append=True)
        df.ta.bbands(append=True)

        df['future_price_5d'] = df['close'].shift(-5)
        df['target_binary_5d'] = (df['future_price_5d'] > df['close']).astype(int)

        df.dropna(inplace=True)
        df.drop(columns=['future_price_5d'], inplace=True)

        logger.info(f"Feature calculation complete. DataFrame shape: {df.shape}")
        return df

    def save_features(self, df: pd.DataFrame, symbol: str):
        if df is None or df.empty:
            logger.warning(f"Feature DataFrame for {symbol} is empty. Nothing to save.")
            return

        blob_name = f"{symbol}/features.parquet"
        logger.info(f"Saving features to {blob_name}...")

        try:
            parquet_buffer = BytesIO()
            df.to_parquet(parquet_buffer, index=True)
            parquet_buffer.seek(0)

            if self.use_azure:
                self.azure_manager.upload_blob(blob_name, parquet_buffer.getvalue())
            else:
                local_path = os.path.join("features", symbol)
                os.makedirs(local_path, exist_ok=True)
                with open(os.path.join(local_path, "features.parquet"), "wb") as f:
                    f.write(parquet_buffer.getvalue())

            logger.info(f"Successfully saved features for {symbol}.")
        except Exception as e:
            logger.error(f"Failed to save features for {symbol}: {e}", exc_info=True)


if __name__ == '__main__':
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA',
        'JPM', 'BAC', 'WFC', 'GS',
    ]

    pipeline = FeaturePipeline(use_azure=True)
    for stock_symbol in stocks:
        pipeline.run_pipeline(stock_symbol)