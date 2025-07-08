import sys
import os
import logging
import pandas as pd
import joblib
import io

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler

from data_collection.azure_data_manager import AzureDataManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class ModelTrainer:
    def __init__(self, model_dir="trained_models", use_azure=True):
        self.model_dir = model_dir
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

        self.use_azure = use_azure
        if self.use_azure:
            self.azure_manager = AzureDataManager(container_name="features")
        else:
            self.azure_manager = None


    def train_model(self, symbol: str, target_column: str = "target_binary_5d"):
        logger.info(f"📈 Loading features for {symbol}...")

        df = self._load_features(symbol)
        if df is None or df.empty:
            logger.error(f"⚠️ No features available for {symbol}. Skipping training.")
            return

        if target_column not in df.columns:
            logger.error(f"⚠️ Target column '{target_column}' not found in data for {symbol}")
            return

        df.dropna(subset=[target_column], inplace=True)

        X = df.drop(columns=[target_column])
        y = df[target_column]

        X = X.select_dtypes(include=["float64", "int64"]).fillna(0) # Fill NaNs in features

        if X.empty:
            logger.error("No features left after cleaning. Stopping.")
            return

        logger.info(f"📊 Training set has {X.shape[1]} features and {X.shape[0]} rows.")

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1
        )

        logger.info("🧠 Training model...")
        model.fit(X_train_scaled, y_train)

        preds = model.predict(X_test_scaled)
        acc = accuracy_score(y_test, preds)
        logger.info(f"✅ Accuracy on test set: {acc:.4f}")
        logger.info("\n" + classification_report(y_test, preds))

        importances = pd.Series(model.feature_importances_, index=X.columns)
        logger.info("📌 Top 10 Feature Impertances:")
        logger.info(importances.sort_values(ascending=False).head(10))

        self._save_model(symbol, model, scaler)

    def _load_features(self, symbol: str) -> pd.DataFrame:
        blob_name = f"{symbol}/features.parquet"

        try:
            if self.use_azure:
                logger.info(f"🔄 Downloading {blob_name} from Azure Blob Storage...")
                data_bytes = self.azure_manager.load_data_from_blob(blob_name)
                if data_bytes is None:
                    return None
                df = pd.read_parquet(io.BytesIO(data_bytes))
            else:
                local_path = os.path.join("features", symbol, "features.parquet")
                df = pd.read_parquet(local_path)
            return df
        except Exception as e:
            logger.error(f"Failed to load features for {symbol}: {e}")
            return None


    def _save_model_to_azure(self, symbol: str, model, scaler):
        try:
            import io
            import joblib

            model_package = {
                'model': model,
                'scaler': scaler,
                'features': list(model.feature_names_in_),
                'created_at': datetime.now().isoformat()
            }

            buffer = io.BytesIO()
            joblib.dump(model_package, buffer)
            buffer.seek(0)

            blob_name = f"models/{symbol}/latest_model.pkl"

            from data_collection.azure_storage import AzureDataManager
            azure_manager = AzureDataManager()
            azure_manager.save_data_to_blob(blob_name, buffer.getvalue())

            logger.info(f"✅ Model package saved to Azure: {blob_name}")

        except Exception as e:
            logger.error(f"❌ Failed to save model to Azure: {e}")

    def _save_model(self, symbol: str, model, scaler):
        model_path = os.path.join(self.model_dir, f"{symbol}_model.joblib")
        scaler_path = os.path.join(self.model_dir, f"{symbol}_scaler.joblib")

        try:
            joblib.dump(model, model_path)
            joblib.dump(scaler, scaler_path)
            logger.info(f"✅ Model saved locally to {model_path}")
            logger.info(f"✅ Scaler saved locally to {scaler_path}")

            self._save_model_to_azure(symbol, model, scaler)

        except Exception as e:
            logger.error(f"❌ Failed to save model: {e}")