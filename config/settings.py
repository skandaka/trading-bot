import os
from dotenv import load_dotenv

load_dotenv()

class AppConfig:
    def __init__(self):
        self.storage_connection = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.cosmos_connection = os.getenv("COSMOS_DB_CONNECTION_STRING")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY")

        if not self.storage_connection or not self.cosmos_connection:
            raise ValueError("One or more Azure connection strings are missing from the .env file.")

config = AppConfig()