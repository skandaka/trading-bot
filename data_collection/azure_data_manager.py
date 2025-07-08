import os
import logging
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class AzureDataManager:
    def __init__(self, container_name: str):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING environment variable not set.")

        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
        self.container_name = container_name
        logger.info(f"AzureDataManager initialized for container: '{self.container_name}'")

    def create_container_if_not_exists(self):
        try:
            self.blob_service_client.create_container(self.container_name)
            logger.info(f"Container '{self.container_name}' created successfully.")
        except ResourceExistsError:
            logger.info(f"Container '{self.container_name}' already exists.")
        except Exception as e:
            logger.error(f"Failed to create container '{self.container_name}': {e}")

    def upload_blob(self, blob_name: str, data: bytes):
        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)
            blob_client.upload_blob(data, overwrite=True)
            logger.info(f"Successfully uploaded to {blob_name} in container {self.container_name}.")
        except Exception as e:
            logger.error(f"Failed to upload blob '{blob_name}': {e}", exc_info=True)

    def load_data_from_blob(self, blob_name: str) -> bytes:
        try:
            blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)

            if not blob_client.exists():
                logger.warning(f"Blob '{blob_name}' not found in container '{self.container_name}'.")
                return None

            downloader = blob_client.download_blob()
            return downloader.readall()
        except Exception as e:
            logger.error(f"Failed to download blob '{blob_name}' from container '{self.container_name}': {e}")
            return None