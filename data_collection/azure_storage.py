import os
import logging
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureDataManager:
    def __init__(self):
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not self.connection_string:
            raise ValueError("Azure Storage connection string not found in .env file.")
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)

    def save_data_to_blob(self, blob_name, data, container_name="market-data"):
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            container_client.get_container_properties()
        except Exception:
            container_client.create_container()
            logger.info(f"Container '{container_name}' created.")

        try:
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(data, overwrite=True)
            logger.info(f"Successfully saved data to {container_name}/{blob_name}")
        except Exception as e:
            logger.error(f"Failed to save to blob: {e}")
            raise