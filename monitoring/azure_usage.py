from azure.storage.blob import BlobServiceClient
from azure.cosmos import CosmosClient
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def check_azure_usage():
    print("Azure Resource Usage Report")
    print("=" * 50)
    print(f"Generated at: {datetime.now()}")
    print()

    try:
        blob_service = BlobServiceClient.from_connection_string(
            os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        )

        containers = list(blob_service.list_containers())
        print(f"Blob Storage Containers: {len(containers)}")

        total_blobs = 0
        for container in containers:
            container_client = blob_service.get_container_client(container['name'])
            blobs = list(container_client.list_blobs())
            total_blobs += len(blobs)
            print(f"  - {container['name']}: {len(blobs)} blobs")

        print(f"Total blobs: {total_blobs}")

    except Exception as e:
        print(f"Error checking Blob Storage: {e}")

    print()

    # check Cosmos DB
    try:
        cosmos_client = CosmosClient.from_connection_string(
            os.getenv('COSMOS_DB_CONNECTION_STRING')
        )

        database = cosmos_client.get_database_client('TradingBot')
        containers = list(database.list_containers())

        print(f"Cosmos DB Containers: {len(containers)}")
        for container in containers:
            container_client = database.get_container_client(container['id'])
            print(f"  - {container['id']}")

    except Exception as e:
        print(f"Error checking Cosmos DB: {e}")

    print()
    print("Note: Check Azure Portal for detailed cost information")
    print("Student credits remaining: Check at https://www.microsoftazuresponsorships.com/")


if __name__ == "__main__":
    check_azure_usage()