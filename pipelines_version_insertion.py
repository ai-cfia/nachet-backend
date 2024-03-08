import os
import json

from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError

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


def insert_new_version_pipeline(
        pipelines_json: dict,
        connection_string: str,
        pipeline_container_name: str
    ) -> bool:
    """
    Inserts a new version of a pipeline JSON into an Azure Blob Storage
    container.

    Args:
        pipelines_json (dict): The JSON data of the pipeline. connection_string
        (str): The connection string for the Azure Blob Storage account.
        pipeline_container_name (str): The name of the container where the
        pipeline JSON will be uploaded.

    Returns:
        bool: True if the pipeline JSON was successfully uploaded, False
        otherwise.
    """
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )

        container_client = blob_service_client.get_container_client(
            pipeline_container_name
        )

        json_name = "{}/{}.json".format("pipelines", pipelines_json.get("version"))
        container_client.upload_blob(
            json_name, json.dumps(pipelines_json, indent=4), overwrite=False)
        return "The pipeline was successfully uploaded to the blob storage"

    except (ValueError, ResourceExistsError) as error:
        raise ConnectionStringError(error.args[0]) from error


def pipeline_insertion(json_path:str):

    if not os.path.exists(json_path):
        raise PipelineInsertionError(
            f"The file does not exist, please check the file path\n provided path{json_path}")

    if json_path.split(".")[-1] != "json":
        raise PipelineInsertionError(
            "The file must be a json file, please check the file extension")

    try:
        cipher_suite = Fernet(KEY)

        with (open(json_path, "r")) as file:
            pipelines_json = file.read()

        pipelines_json = json.loads(pipelines_json)

        if not isinstance(pipelines_json, dict):
            raise PipelineInsertionError(
                f"The file must contain a dictionary with the following keys: version, date, pipelines, models \
                    \n instead provided a {type(pipelines_json)}")


        for model in pipelines_json["models"]:
            # crypting endopoint
            endpoint = model["endpoint"].encode()
            model["endpoint"] = cipher_suite.encrypt(endpoint).decode()
            # crypting api_key
            api_key = model["api_key"].encode()
            model["api_key"] = cipher_suite.encrypt(api_key).decode()

        return insert_new_version_pipeline(
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
            # Add the given path
            print("Please provide the path to the json file as an argument")

        if isinstance(error, PipelineInsertionError):
            print(error.args[0])

if __name__ == "__main__":
    quit(main())
