import pandas as pd
import numpy as np
import logging
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_validation import DataValidator
import pandas_ta as ta

logging.getLogger('pandas_ta').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class FeatureEngineer:
    def __init__(self):
        self.validator = DataValidator()
        self.feature_names = []

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        custom_strategy = ta.Strategy(
            name="MasterStrategy",
            description="Comprehensive feature set for trading models",
            ta=[
                {"kind": "sma", "length": 20},
                {"kind": "sma", "length": 50},
                {"kind": "ema", "length": 12},
                {"kind": "ema", "length": 26},
                {"kind": "rsi"},
                {"kind": "macd"},
                {"kind": "bbands"},
                {"kind": "atr"},
                {"kind": "obv"},
                {"kind": "adx"},
                {"kind": "cci"},
                {"kind": "stoch"},
            ]
        )
        df.ta.strategy(custom_strategy)
        df['returns_1d'] = df['Close'].pct_change(1)
        df['log_returns'] = np.log(df['Close'] / df['Close'].shift(1))
        df['volatility_20d'] = df['returns_1d'].rolling(20).std()
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        self.feature_names = df.columns.tolist()
        return df

    def create_target_variables(self, df, horizon=5):
        df[f'target_binary_{horizon}d'] = (df['Close'].shift(-horizon) > df['Close']).astype(int)
        return df

    def validate_features(self, df):
        return self.validator.validate_features(df)