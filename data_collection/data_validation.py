import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    def validate_features(self, df: pd.DataFrame):
        numeric_df = df.select_dtypes(include=np.number)

        if np.isinf(numeric_df).values.any():
            logger.warning("Infinite values found, replacing with NaN.")
            df.replace([np.inf, -np.inf], np.nan, inplace=True)

        if df.isnull().values.any():
            logger.warning("NaN values found, applying forward/backward fill.")
            df.fillna(method='ffill', inplace=True)
            df.fillna(method='bfill', inplace=True)
            df.dropna(inplace=True)

        return df