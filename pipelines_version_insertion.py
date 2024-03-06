import os
import json
import asyncio

import azure_storage.azure_storage_api as azure_storage_api

from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("NACHET_BLOB_PIPELINE_DECRYPTION_KEY")
blob_storage_account_name = os.getenv("NACHET_BLOB_PIPELINE_NAME")
connection_string = os.getenv("NACHET_AZURE_STORAGE_CONNECTION_STRING")

cipher_suite = Fernet(key)

with (open("./mock_pipeline_json.json", "r")) as file:
    pipelines_json = file.read()

pipelines_json = json.loads(pipelines_json)

for model in pipelines_json["models"]:
    # crypting endopoint
    endpoint = model["endpoint"].encode()
    model["endpoint"] = cipher_suite.encrypt(endpoint).decode()
    # crypting api_key
    api_key = model["api_key"].encode()
    model["api_key"] = cipher_suite.encrypt(api_key).decode()

print(azure_storage_api.insert_new_version_pipeline(pipelines_json, connection_string, blob_storage_account_name))

if __name__ == "__main__":
    blob = asyncio.run(azure_storage_api.get_pipeline_info("connection_string", blob_storage_account_name, "0.1.0"))
