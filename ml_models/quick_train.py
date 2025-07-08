import sys
import os
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.model_trainer import ModelTrainer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    stocks_to_train = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', # Tech
        'JPM', 'BAC', 'WFC', 'GS', # Financials
    ]

    logging.info("🚀 Starting model training session...")
    trainer = ModelTrainer(use_azure=True)

    for stock in stocks_to_train:
        logging.info(f"--- Training model for {stock} ---")
        try:
            trainer.train_model(symbol=stock, target_column="target_binary_5d")
        except Exception as e:
            logging.error(f"💥 An unexpected error occurred during training for {stock}: {e}", exc_info=True)
        logging.info(f"--- Finished training process for {stock} ---\n")

if __name__ == "__main__":
    main()