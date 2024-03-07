import os
import json

import azure_storage.azure_storage_api as azure_storage_api

from sys import argv
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from custom_exceptions import ConnectionStringError

load_dotenv()

KEY = os.getenv("NACHET_BLOB_PIPELINE_DECRYPTION_KEY")
BLOB_STORAGE_ACCOUNT_NAME = os.getenv("NACHET_BLOB_PIPELINE_NAME")
CONNECTION_STRING = os.getenv("NACHET_AZURE_STORAGE_CONNECTION_STRING")


class PipelineInsertionError(Exception):
    pass


def pipeline_insertion(json_path:str):

    if not os.path.exists(json_path):
        raise PipelineInsertionError(
            "The file does not exist, please check the file path")

    if json_path.split(".")[-1] != "json":
        raise PipelineInsertionError(
            "The file must be a json file, please check the file extension")

    try:
        cipher_suite = Fernet(KEY)

        with (open(json_path, "r")) as file:
            pipelines_json = file.read()

        pipelines_json = json.loads(pipelines_json)

        for model in pipelines_json["models"]:
            # crypting endopoint
            endpoint = model["endpoint"].encode()
            model["endpoint"] = cipher_suite.encrypt(endpoint).decode()
            # crypting api_key
            api_key = model["api_key"].encode()
            model["api_key"] = cipher_suite.encrypt(api_key).decode()

        return azure_storage_api.insert_new_version_pipeline(
            pipelines_json, CONNECTION_STRING, BLOB_STORAGE_ACCOUNT_NAME)

    except (ConnectionStringError) as error:
        raise PipelineInsertionError(
            f"An error occurred while uploading the file to the blob storage: {error.args[0]}") from error


def main():
    try:
        json_path = argv[1]
        print(pipeline_insertion(json_path))
    except (IndexError, PipelineInsertionError) as error:
        if isinstance(error, IndexError):
            print("Please provide the path to the json file as an argument")

        if isinstance(error, PipelineInsertionError):
            print(error.args[0])

if __name__ == "__main__":
    quit(main())
