import os
import pandas as pd
from datetime import datetime
import logging
import io
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from feature_engineering import FeatureEngineer
from azure_storage import AzureDataManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataPipeline:
    def __init__(self):
        self.feature_engineer = FeatureEngineer()
        self.azure_manager = AzureDataManager()
        self.local_data_dir = "local_data_cache"
        self.all_stocks = [f.split('.')[0] for f in os.listdir(self.local_data_dir) if f.endswith('.csv')]
        self.stats = {'processed': 0, 'failed': 0}

    def run_pipeline(self):
        logger.info(f"Starting pipeline from LOCAL CACHE for {len(self.all_stocks)} stocks...")

        for symbol in self.all_stocks:
            try:
                file_path = os.path.join(self.local_data_dir, f"{symbol}.csv")

                hist_data = pd.read_csv(
                    file_path,
                    index_col=0,
                    parse_dates=True,
                    date_parser=lambda x: pd.to_datetime(x, format="%Y-%m-%d", errors='coerce')
                )

                hist_data = hist_data.apply(pd.to_numeric, errors='coerce')
                hist_data.dropna(subset=["Open", "High", "Low", "Close", "Volume"], inplace=True)
                features_df = self.feature_engineer.create_features(hist_data)
                features_df = self.feature_engineer.create_target_variables(features_df)
                features_df = self.feature_engineer.validate_features(features_df)

                self._save_features(symbol, features_df)
                self.stats['processed'] += 1
            except Exception as e:
                logger.error(f"Pipeline failed for {symbol}: {e}")
                self.stats['failed'] += 1

        logger.info("=" * 50)
        logger.info(f"PIPELINE COMPLETE. Success: {self.stats['processed']}, Failed: {self.stats['failed']}")

    def _save_features(self, symbol, df):
        buffer = io.BytesIO()
        df.to_parquet(buffer, index=True)
        blob_name = f"features/{symbol}/features.parquet"
        self.azure_manager.save_data_to_blob(blob_name, buffer.getvalue())


if __name__ == "__main__":
    pipeline = DataPipeline()
    pipeline.run_pipeline()