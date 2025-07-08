
import os
import sys
import time
import subprocess
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command: str, description: str):
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Starting: {description}")
    logger.info(f"Command: {command}")
    logger.info(f"{'=' * 60}")

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        duration = time.time() - start_time

        if result.returncode == 0:
            logger.info(f"✅ {description} completed successfully in {duration:.2f} seconds")
            return True
        else:
            logger.error(f"❌ {description} failed with return code {result.returncode}")
            return False

    except Exception as e:
        logger.error(f"❌ Error running {description}: {str(e)}")
        return False


def main():
    start_time = datetime.now()
    logger.info(f"Starting complete pipeline at {start_time.strftime('%I:%M %p')}")
    logger.info(f"Target completion: 2:30 PM")

    if not run_command(
            "python data_collection/data_pipeline.py",
            "Data Collection Pipeline"
    ):
        logger.error("Data pipeline failed. Please check the logs and fix any issues.")
        return

    logger.info("Waiting 10 seconds for Azure sync...")
    time.sleep(10)

    if not run_command(
            "python ml_models/quick_train.py",
            "Model Training"
    ):
        logger.error("Model training failed. Please check if features were created successfully.")
        return

    logger.info("Waiting 5 seconds for model saves...")
    time.sleep(5)

    logger.info("\n" + "=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("You can now run:")
    logger.info("  1. python main.py demo - For the full demo")
    logger.info("  2. streamlit run dashboard/app.py - For just the dashboard")
    logger.info("=" * 60)

    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    logger.info(f"\nTotal pipeline execution time: {total_duration / 60:.1f} minutes")
    logger.info(f"Completed at: {end_time.strftime('%I:%M %p')}")


if __name__ == "__main__":
    main()