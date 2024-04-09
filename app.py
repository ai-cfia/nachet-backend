import urllib.request
import json
import os
import base64
import re
import time
import model.inference as inference
from model import request_function

from datetime import date
from dotenv import load_dotenv
from quart import Quart, request, jsonify
from quart_cors import cors
from collections import namedtuple
from cryptography.fernet import Fernet
import azure_storage.azure_storage_api as azure_storage_api

from custom_exceptions import (
    DeleteDirectoryRequestError,
    ListDirectoriesRequestError,
    InferenceRequestError,
    CreateDirectoryRequestError,
    ServerError,
    PipelineNotFoundError,
    ConnectionStringError
)

load_dotenv()
connection_string_regex = r"^DefaultEndpointsProtocol=https?;.*;FileEndpoint=https://[a-zA-Z0-9]+\.file\.core\.windows\.net/;$"
connection_string = os.getenv("NACHET_AZURE_STORAGE_CONNECTION_STRING")


FERNET_KEY = os.getenv("NACHET_BLOB_PIPELINE_DECRYPTION_KEY")
PIPELINE_VERSION = os.getenv("NACHET_BLOB_PIPELINE_VERSION")
PIPELINE_BLOB_NAME = os.getenv("NACHET_BLOB_PIPELINE_NAME")

NACHET_DATA = os.getenv("NACHET_DATA")
NACHET_MODEL = os.getenv("NACHET_MODEL")

try:
    MAX_CONTENT_LENGTH = int(os.getenv("NACHET_MAX_CONTENT_LENGTH"))
except (TypeError, ValueError):
    MAX_CONTENT_LENGTH = 16


Model = namedtuple(
    'Model',
    [
        'request_function',
        'name',
        'endpoint',
        'api_key',
        'content_type',
        'deployment_platform',
    ]
)

CACHE = {
    "seeds": None,
    "endpoints": None,
    "pipelines": {},
}

app = Quart(__name__)
app = cors(app, allow_origin="*", allow_methods=["GET", "POST", "OPTIONS"])
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH * 1024 * 1024


@app.post("/del")
async def delete_directory():
    """
    deletes a directory in the user's container
    """
    try:
        data = await request.get_json()
        container_name = data["container_name"]
        folder_name = data["folder_name"]
        if container_name and folder_name:
            container_client = await azure_storage_api.mount_container(
                app.config["BLOB_CLIENT"], container_name, create_container=False
            )
            if container_client:
                folder_uuid = await azure_storage_api.get_folder_uuid(
                    container_client, folder_name
                )
                if folder_uuid:
                    blob_list = container_client.list_blobs()
                    for blob in blob_list:
                        if blob.name.split("/")[0] == folder_uuid:
                            container_client.delete_blob(blob.name)
                    return jsonify([True]), 200
                else:
                    return jsonify(["directory does not exist"]), 400
            else:
                return jsonify(["failed to mount container"]), 400
        else:
            return jsonify(["missing container or directory name"]), 400

    except DeleteDirectoryRequestError as error:
        print(error)
        return jsonify(["DeleteDirectoryRequestError: " + str(error)]), 400


@app.post("/dir")
async def list_directories():
    """
    lists all directories in the user's container
    """
    try:
        data = await request.get_json()
        container_name = data["container_name"]
        if container_name:
            container_client = await azure_storage_api.mount_container(
                app.config["BLOB_CLIENT"], container_name, create_container=True
            )
            response = await azure_storage_api.get_directories(container_client)
            return jsonify(response), 200
        else:
            return jsonify(["Missing container name"]), 400

    except ListDirectoriesRequestError as error:
        print(error)
        return jsonify(["ListDirectoriesRequestError: " + str(error)]), 400


@app.post("/create-dir")
async def create_directory():
    """
    creates a directory in the user's container
    """
    try:
        data = await request.get_json()
        container_name = data["container_name"]
        folder_name = data["folder_name"]
        if container_name and folder_name:
            container_client = await azure_storage_api.mount_container(
                app.config["BLOB_CLIENT"], container_name, create_container=False
            )
            response = await azure_storage_api.create_folder(
                container_client, folder_name
            )
            if response:
                return jsonify([True]), 200
            else:
                return jsonify(["directory already exists"]), 400
        else:
            return jsonify(["missing container or directory name"]), 400

    except CreateDirectoryRequestError as error:
        print(error)
        return jsonify(["CreateDirectoryRequestError: " + str(error)]), 400


@app.post("/inf")
async def inference_request():
    """
    Performs inference on an image, and returns the results.
    The image and inference results are uploaded to a folder in the user's container.
    """

    seconds = time.perf_counter() # TODO: transform into logging
    try:
        print(f"{date.today()} Entering inference request") # TODO: Transform into logging
        data = await request.get_json()
        pipeline_name = data.get("model_name")
        folder_name = data["folder_name"]
        container_name = data["container_name"]
        imageDims = data["imageDims"]
        image_base64 = data["image"]

        area_ratio = data.get("area_ratio", 0.5)
        color_format = data.get("color_format", "hex")

        print(f"Requested by user: {container_name}") # TODO: Transform into logging
        pipelines_endpoints = CACHE.get("pipelines")
        blob_service_client = app.config.get("BLOB_CLIENT")

        if not (folder_name and container_name and imageDims and image_base64):
            raise InferenceRequestError(
                "missing request arguments: either folder_name, container_name, imageDims or image is missing")

        if not pipelines_endpoints.get(pipeline_name):
            raise InferenceRequestError(f"model {pipeline_name} not found")

        header, encoded_data = image_base64.split(",", 1)

        # Validate image header #TODO with magic header
        if not header.startswith("data:image/"):
            raise InferenceRequestError("invalid image header")

        # Keep track of every output given by the models
        # TODO: add it to CACHE variable
        cache_json_result = [encoded_data]
        image_bytes = base64.b64decode(encoded_data)

        container_client = await azure_storage_api.mount_container(
            blob_service_client, container_name, create_container=True
        )
        hash_value = await azure_storage_api.generate_hash(image_bytes)
        await azure_storage_api.upload_image(
            container_client, folder_name, image_bytes, hash_value
        )

        for idx, model in enumerate(pipelines_endpoints.get(pipeline_name)):
            print(f"Entering {model.name.upper()} model") # TODO: Transform into logging
            result_json = await model.request_function(model, cache_json_result[idx])
            cache_json_result.append(result_json)

        print("End of inference request") # TODO: Transform into logging
        print("Process results") # TODO: Transform into logging

        processed_result_json = await inference.process_inference_results(
            cache_json_result[-1], imageDims, area_ratio, color_format
        )

        result_json_string = json.dumps(processed_result_json)

        # upload the inference results to the user's container as async task
        app.add_background_task(
            azure_storage_api.upload_inference_result,
            container_client,
            folder_name,
            result_json_string,
            hash_value,
        )
        # return the inference results to the client
        print(f"Took: {'{:10.4f}'.format(time.perf_counter() - seconds)} seconds") # TODO: Transform into logging
        return jsonify(processed_result_json), 200

    except (KeyError, InferenceRequestError) as error:
        print(error)
        return jsonify(["InferenceRequestError: " + error.args[0]]), 400

    except Exception as error:
        print(error)
        return jsonify(["Unexpected error occured"]), 500

@app.get("/coffee")
async def get_coffee():
    return jsonify("Tea is great!"), 418


@app.get("/seed-data/<seed_name>")
async def get_seed_data(seed_name):
    """
    Returns JSON containing requested seed data
    """
    if seed_name in CACHE['seeds']:
        return jsonify(CACHE['seeds'][seed_name]), 200
    else:
        return jsonify(f"No information found for {seed_name}."), 400


@app.get("/reload-seed-data")
async def reload_seed_data():
    """
    Reloads seed data JSON document from Nachet-Data
    """
    try:
        await fetch_json(NACHET_DATA, 'seeds', "seeds/all.json")
        return jsonify(["Seed data reloaded successfully"]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/model-endpoints-metadata")
async def get_model_endpoints_metadata():
    """
    Returns JSON containing the deployed endpoints' metadata
    """
    if CACHE['endpoints']:
        return jsonify(CACHE['endpoints']), 200
    else:
        return jsonify("Error retrieving model endpoints metadata.", 404)


@app.get("/health")
async def health():
    return "ok", 200


@app.get("/test")
async def test():
    # Build test pipeline
    CACHE["endpoints"] = [
                {
                    "pipeline_name": "test_pipeline",
                    "models": ["test_model1"]
                }
            ]
    # Built test model
    m = Model(
        request_function["test"],
        "test_model1",
        "http://localhost:8080/test_model1",
        "test_api_key",
        "application/json",
        "test_platform"
    )

    CACHE["pipelines"]["test_pipeline"] = (m,)

    return CACHE["endpoints"], 200

async def fetch_json(repo_URL, key, file_path):
    """
    Fetches JSON document from a GitHub repository and caches it
    """
    try:
        if key != "endpoints":
            json_url = os.path.join(repo_URL, file_path)
            with urllib.request.urlopen(json_url) as response:
                result = response.read()
                result_json = json.loads(result.decode("utf-8"))
            return result_json

    except urllib.error.HTTPError as error:
        raise ValueError(str(error))
    except Exception as e:
        raise ValueError(str(e))


async def get_pipelines():
    """
    Retrieves the pipelines from the Azure storage API.

    Returns:
    - list: A list of dictionaries representing the pipelines.
    """
    try:
        app.config["BLOB_CLIENT"] = await azure_storage_api.get_blob_client(connection_string)
        result_json = await azure_storage_api.get_pipeline_info(app.config["BLOB_CLIENT"], PIPELINE_BLOB_NAME, PIPELINE_VERSION)
        cipher_suite = Fernet(FERNET_KEY)
    except (ConnectionStringError, PipelineNotFoundError) as error:
        print(error)
        raise ServerError("server errror: could not retrieve the pipelines") from error

    models = ()
    for model in result_json.get("models"):
        m = Model(
            request_function.get(model.get("api_call_function")),
            model.get("model_name"),
            # To protect sensible data (API key and model endpoint), we encrypt it when
            # it's pushed into the blob storage. Once we retrieve the data here in the
            # backend, we need to decrypt the byte format to recover the original
            # data.
            cipher_suite.decrypt(model.get("endpoint").encode()).decode(),
            cipher_suite.decrypt(model.get("api_key").encode()).decode(),
            model.get("content_type"),
            model.get("deployment_platform")
        )
        models += (m,)
    # Build the pipeline to call the models in order in the inference request
    for pipeline in result_json.get("pipelines"):
        CACHE["pipelines"][pipeline.get("pipeline_name")] = tuple([m for m in models if m.name in pipeline.get("models")])

    return result_json.get("pipelines")


@app.before_serving
async def before_serving():
    try:
        # Check: do environment variables exist?
        if connection_string is None:
            raise ServerError("Missing environment variable: NACHET_AZURE_STORAGE_CONNECTION_STRING")

        if FERNET_KEY is None:
            raise ServerError("Missing environment variable: FERNET_KEY")

        # Check: are environment variables correct?
        if not bool(re.match(connection_string_regex, connection_string)):
            raise ServerError("Incorrect environment variable: NACHET_AZURE_STORAGE_CONNECTION_STRING")

        CACHE["seeds"] = await fetch_json(NACHET_DATA, "seeds", "seeds/all.json")
        CACHE["endpoints"] = await get_pipelines()

        print(
            f"""Server start with current configuration:\n
                date: {date.today()}
                file version of pipelines: {PIPELINE_VERSION}
                pipelines: {[pipeline for pipeline in CACHE["pipelines"].keys()]}\n
            """
        ) #TODO Transform into logging

    except ServerError as e:
        print(e)
        raise

    except Exception as e:
        print(e)
        raise ServerError("Failed to retrieve data from the repository")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
