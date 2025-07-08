import os
import sys
import logging
import joblib
import pandas as pd
from alpaca_trade_api.rest import REST, TimeFrame
import pandas_ta as ta  # Make sure pandas_ta is imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TradingEngine:
    def __init__(self, symbol: str, model_dir="trained_models"):
        self.symbol = symbol
        self.model_path = os.path.join(model_dir, f"{self.symbol}_model.joblib")
        self.scaler_path = os.path.join(model_dir, f"{self.symbol}_scaler.joblib")
        self.model = None
        self.scaler = None

        self.api = REST(
            key_id=os.getenv("ALPACA_API_KEY"),
            secret_key=os.getenv("ALPACA_SECRET_KEY"),
            base_url=os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        )

        self.load_model()

    def load_model(self):
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                logger.info(f"✅ Model and scaler for {self.symbol} loaded successfully.")
            else:
                logger.error(f"❌ Model or scaler not found for {self.symbol}. Please train first.")
        except Exception as e:
            logger.error(f"Failed to load model for {self.symbol}: {e}")

    def get_latest_data(self) -> pd.DataFrame:
        logger.info(f"Fetching latest market data for {self.symbol}...")
        try:
            bars = self.api.get_bars(self.symbol, TimeFrame.Day, limit=100).df

            if bars.empty:
                logger.warning(f"No recent bar data found for {self.symbol}.")
                return None
            return bars
        except Exception as e:
            logger.error(f"Failed to fetch bar data: {e}")
            return None

    def generate_prediction(self) -> int:
        if not self.model or not self.scaler:
            logger.error("Model not loaded, cannot make a prediction.")
            return 0

        latest_data = self.get_latest_data()
        if latest_data is None:
            return 0

        latest_data.ta.sma(length=20, append=True)
        latest_data.ta.sma(length=50, append=True)
        latest_data.ta.ema(length=20, append=True)
        latest_data.ta.rsi(length=14, append=True)
        latest_data.ta.macd(append=True)
        latest_data.ta.bbands(append=True)
        latest_data.dropna(inplace=True)

        if latest_data.empty:
            logger.warning("Not enough data to calculate features for a prediction.")
            return 0

        feature_columns = self.model.feature_names_in_

        missing_cols = [col for col in feature_columns if col not in latest_data.columns]
        if missing_cols:
            logger.error(f"Missing required feature columns: {missing_cols}")
            return 0

        current_features = latest_data[feature_columns]

        scaled_features = self.scaler.transform(current_features)

        prediction = self.model.predict(scaled_features[-1].reshape(1, -1))[0]

        if prediction == 1:
            logger.info(f"🧠 Prediction for {self.symbol}: BUY (1)")
            return 1
        else:
            logger.info(f"🧠 Prediction for {self.symbol}: HOLD/SELL (0)")
            return 0

    def execute_trade(self, signal: int):
        if signal == 1:
            logger.info(f"Executing BUY order for {self.symbol}.")
            try:
                order = self.api.submit_order(
                    symbol=self.symbol,
                    qty=10,
                    side='buy',
                    type='market',
                    time_in_force='gtc'
                )
                logger.info(f"✅ BUY order submitted for {self.symbol}. Order ID: {order.id}")
            except Exception as e:
                logger.error(f"❌ Failed to submit BUY order for {self.symbol}: {e}")

    def run(self):
        logger.info(f"--- Running Trading Engine for {self.symbol} ---")
        signal = self.generate_prediction()
        self.execute_trade(signal)