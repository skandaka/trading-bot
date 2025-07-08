import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import joblib
import logging
import io
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import config
from data_collection.azure_storage import AzureDataManager
from data_collection.feature_engineering import FeatureEngineer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PaperTradingEngine:
    def __init__(self, initial_capital=100000):
        self.azure_manager = AzureDataManager()
        self.feature_engineer = FeatureEngineer()
        self.container_name = "market-data"
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.positions = {}
        self.trade_history = []
        self.models = {}
        self.local_data_dir = "local_data_cache"
        self.local_data = self._load_all_local_data()

        self.load_models()

    def _load_all_local_data(self):
        data = {}
        if not os.path.exists(self.local_data_dir):
            logger.error(
                f"Local data cache not found at '{self.local_data_dir}'. Please run `create_local_cache.py` first.")
            return data

        for file in os.listdir(self.local_data_dir):
            if file.endswith('.csv'):
                symbol = file.split('.')[0]
                try:
                    df_temp = pd.read_csv(os.path.join(self.local_data_dir, file), nrows=1)
                    logger.info(f"CSV columns for {symbol}: {list(df_temp.columns)}")
                    file_path = os.path.join(self.local_data_dir, file)

                    if 'Date' in df_temp.columns:
                        data[symbol] = pd.read_csv(file_path, index_col='Date', parse_dates=True)
                    elif 'Datetime' in df_temp.columns:
                        data[symbol] = pd.read_csv(file_path, index_col='Datetime', parse_dates=True)
                    else:
                        data[symbol] = pd.read_csv(file_path, index_col=0, parse_dates=True)

                    logger.info(f"✅ Loaded {len(data[symbol])} rows for {symbol}")

                except Exception as e:
                    logger.error(f"❌ Failed to load {symbol}: {e}")
                    try:
                        data[symbol] = pd.read_csv(os.path.join(self.local_data_dir, file))
                        logger.info(f"⚠️ Loaded {symbol} without date parsing")
                    except:
                        logger.error(f"💥 Completely failed to load {symbol}")

        logger.info(f"Loaded {len(data)} stocks into local data cache for trading simulation.")
        return data

    def load_models(self):
        for symbol in self.local_data.keys():
            try:
                blob_name = f"models/{symbol}/latest_model.pkl"
                blob_client = self.azure_manager.blob_service_client.get_blob_client(container=self.container_name,
                                                                                     blob=blob_name)
                model_data = blob_client.download_blob().readall()
                self.models[symbol] = joblib.load(io.BytesIO(model_data))
                logger.info(f"Loaded model for {symbol}")
            except Exception:
                logger.warning(f"No trained model found for {symbol}. It will be skipped.")

    def get_simulated_price(self, symbol):
        if symbol in self.local_data:
            return self.local_data[symbol]['Close'].tail(50).sample(1).iloc[0]
        return None

    def get_live_features(self, symbol):
        if symbol not in self.local_data: return None
        hist_data = self.local_data[symbol]
        features_df = self.feature_engineer.create_features(hist_data)
        return features_df.tail(1)

    def get_prediction(self, symbol: str) -> dict:
        default = {'action': 'HOLD', 'confidence': 0.0}
        if symbol not in self.models: return default

        try:
            live_features_df = self.get_live_features(symbol)
            if live_features_df is None: return default

            model_payload = self.models[symbol]
            model = model_payload['model']
            model_features = model_payload['features']

            live_features = live_features_df[model_features].fillna(0)

            prediction = model.predict(live_features)[0]
            confidence = model.predict_proba(live_features)[0].max()

            action = 'BUY' if prediction == 1 else 'SELL'
            if confidence < 0.65: action = 'HOLD'

            return {'action': action, 'confidence': float(confidence)}
        except Exception as e:
            logger.error(f"Prediction error for {symbol}: {e}")
            return default

    def execute_trade(self, symbol: str, action: str, price: float):
        trade_value = self.capital * 0.05  # Use 5% of capital per trade
        quantity = int(trade_value / price)
        if quantity == 0: return

        trade = {'timestamp': datetime.now().isoformat(), 'symbol': symbol, 'action': action, 'quantity': quantity,
                 'price': price}

        if action == 'BUY' and symbol not in self.positions:
            self.positions[symbol] = {'quantity': quantity, 'buy_price': price}
            self.capital -= quantity * price
            self.trade_history.append(trade)
            logger.info(f"SIMULATED BUY: {quantity} {symbol} @ ${price:.2f}")

        elif action == 'SELL' and symbol in self.positions:
            pos = self.positions.pop(symbol)
            self.capital += pos['quantity'] * price
            trade['profit'] = (price - pos['buy_price']) * pos['quantity']
            self.trade_history.append(trade)
            logger.info(f"SIMULATED SELL: {pos['quantity']} {symbol} @ ${price:.2f}, P/L: ${trade['profit']:.2f}")

    def update_portfolio(self):
        total_value = self.capital
        for symbol, pos in self.positions.items():
            current_price = self.get_simulated_price(symbol)
            if current_price:
                market_value = current_price * pos['quantity']
                pos['current_price'] = current_price
                pos['pnl'] = (current_price - pos['buy_price']) * pos['quantity']
                total_value += market_value
        return {'cash': self.capital, 'positions': self.positions, 'total_value': total_value,
                'total_return': ((total_value - self.initial_capital) / self.initial_capital) * 100}

    def save_state(self):
        state = {
            'portfolio': self.update_portfolio(),
            'trades': self.trade_history[-20:],
            'timestamp': datetime.now().isoformat()
        }
        self.azure_manager.save_data_to_blob("trading_state/current_state.json", json.dumps(state, indent=2))

    def run_cycle(self):
        logger.info("--- Starting Trading Simulation Cycle ---")
        for symbol in list(self.models.keys()):
            prediction = self.get_prediction(symbol)
            logger.info(f"Prediction for {symbol}: {prediction['action']} (Confidence: {prediction['confidence']:.2%})")
            if prediction['action'] != 'HOLD':
                price = self.get_simulated_price(symbol)
                if price: self.execute_trade(symbol, prediction['action'], price)
        self.save_state()
        logger.info("--- Trading Cycle Complete ---")



if __name__ == '__main__':
    engine = PaperTradingEngine()

    print("🚀 Starting single trading cycle...")
    print("=" * 50)

    engine.run_cycle()

    print("=" * 50)
    print("✅ Trading cycle completed successfully!")
    print(f"💰 Current Portfolio Value: ${engine.update_portfolio()['total_value']:,.2f}")
    print(f"💵 Cash Available: ${engine.capital:,.2f}")
    print(f"🏦 Active Positions: {len(engine.positions)}")
    print(f"📋 Total Trades: {len(engine.trade_history)}")

    exit(0)