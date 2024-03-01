import urllib.request
import json
import os
import base64
import re
import time
import azure_storage.azure_storage_api as azure_storage_api
import model_inference.inference as inference
import model_inference.model_module as model_module

from dotenv import load_dotenv
from quart import Quart, request, jsonify
from quart_cors import cors
from collections import namedtuple
from cryptography.fernet import Fernet

from custom_exceptions import (
    DeleteDirectoryRequestError,
    ListDirectoriesRequestError,
    InferenceRequestError,
    CreateDirectoryRequestError,
    ServerError,
)

load_dotenv()
connection_string_regex = r"^DefaultEndpointsProtocol=https?;.*;FileEndpoint=https://[a-zA-Z0-9]+\.file\.core\.windows\.net/;$"
connection_string = os.getenv("NACHET_AZURE_STORAGE_CONNECTION_STRING")

FERNET_KEY = os.getenv("NACHET_BLOB_PIPELINE_DECRYPTION_KEY")
PIPELINE_VERSION = os.getenv("NACHET_BLOB_PIPELINE_VERSION")
PIPELINE_BLOB_NAME = os.getenv("NACHET_BLOB_PIPELINE_NAME")

NACHET_DATA = os.getenv("NACHET_DATA")
NACHET_MODEL = os.getenv("NACHET_MODEL")

Model = namedtuple(
    'Model',
    [
        'entry_function',
        'name',
        'endpoint',
        'api_key',
        'inference_function',
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
# Turn off for deployment or model testing
app.testing = True


@app.post("/del")
async def delete_directory():
    """
    deletes a directory in the user's container
    """
    try:
        data = await request.get_json()
        connection_string: str = os.environ["NACHET_AZURE_STORAGE_CONNECTION_STRING"]
        container_name = data["container_name"]
        folder_name = data["folder_name"]
        if container_name and folder_name:
            container_client = await azure_storage_api.mount_container(
                connection_string, container_name, create_container=False
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
        connection_string: str = os.environ["NACHET_AZURE_STORAGE_CONNECTION_STRING"]
        container_name = data["container_name"]
        if container_name:
            container_client = await azure_storage_api.mount_container(
                connection_string, container_name, create_container=True
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
        connection_string: str = os.environ["NACHET_AZURE_STORAGE_CONNECTION_STRING"]
        container_name = data["container_name"]
        folder_name = data["folder_name"]
        if container_name and folder_name:
            container_client = await azure_storage_api.mount_container(
                connection_string, container_name, create_container=False
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
     
    seconds = time.perf_counter() # transform into logging
    try:
        print("Entering inference request") # Transform into logging
        data = await request.get_json()
        pipeline_name = data.get("model_name")
        folder_name = data["folder_name"]
        container_name = data["container_name"]
        imageDims = data["imageDims"]
        image_base64 = data["image"]

        pipelines_endpoints = CACHE.get("pipelines")

        if not (folder_name and container_name and imageDims and image_base64):
            return jsonify(["missing request arguments"]), 400
        
        if not pipelines_endpoints.get(pipeline_name):
            return jsonify([f"Model {pipeline_name} not found"]), 400
        
        header, encoded_data = image_base64.split(",", 1)

        # Validate image header
        if not header.startswith("data:image/"):
            return jsonify(["Invalid image header"]), 400
        
        image_bytes = base64.b64decode(encoded_data)
        if not app.testing:
            # This sequence of code is already test in the azure_storage_api test
            container_client = await azure_storage_api.mount_container(
                connection_string, container_name, create_container=True
            )
            hash_value = await azure_storage_api.generate_hash(image_bytes)
            blob_name = await azure_storage_api.upload_image(
                container_client, folder_name, image_bytes, hash_value
            )
            blob = await azure_storage_api.get_blob(container_client, blob_name)
            image_bytes = base64.b64encode(blob).decode("utf8")

        try:
            # Keep track of every output given by the models
            # TO DO add it to CACHE variable
            cache_json_result = [image_bytes]

            for idx, model in enumerate(pipelines_endpoints.get(pipeline_name)):
                print(f"Entering {model.name.upper()} model") # Transform into logging
                result_json = await model.entry_function(model, cache_json_result[idx])
                cache_json_result.append(result_json)

            print("End of inference request") # Transform into logging
            print("Process results") # Transform into logging

            processed_result_json = await inference.process_inference_results(
                cache_json_result[-1], imageDims
            )

        except urllib.error.HTTPError as error:
            print(error)
            return jsonify(["endpoint cannot be reached" + str(error.code)]), 400
        
        # upload the inference results to the user's container as async task
        result_json_string = json.dumps(processed_result_json)

        if not app.testing:
            app.add_background_task(
                azure_storage_api.upload_inference_result,
                container_client,
                folder_name,
                result_json_string,
                hash_value,
            )
        # return the inference results to the client
        print(f"Took: {'{:10.4f}'.format(time.perf_counter() - seconds)} seconds")
        return jsonify(processed_result_json), 200 

    except InferenceRequestError as error:
        print(error)
        return jsonify(["InferenceRequestError: " + str(error)]), 400
    
    except Exception as error:
        print(error)
        return jsonify(["Unexpected error occured"]), 500


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
        return jsonify("Error retrieving model endpoints metadata.", 400)


@app.get("/health")
async def health():
    return "ok", 200


async def fetch_json(repo_URL, key, file_path, mock=False):
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


async def get_pipelines(mock:bool = False):
    """
    Retrieves the pipelines from the Azure storage API.

    Parameters:
    - mock (bool): If True, retrieves the pipelines from a mock JSON file. If False, retrieves the pipelines from the Azure storage API.

    Returns:
    - list: A list of dictionaries representing the pipelines.
    """
    if mock:
        with open("mock_pipeline_json.json", "r+") as f:
            result_json = json.load(f)
    else:
        result_json = await azure_storage_api.get_pipeline_info(connection_string, PIPELINE_BLOB_NAME, PIPELINE_VERSION)
        cipher_suite = Fernet(FERNET_KEY)
    # Get all the api_call function and map them in a dictionary
    api_call_function = {func.split("from_")[1]: getattr(model_module, func) for func in dir(model_module) if "inference" in func.split("_")}
    # Get all the inference functions and map them in a dictionary 
    inference_functions = {func: getattr(inference, func) for func in dir(inference) if "process" in func.split("_")}

    models = ()
    for model in result_json.get("models"):
        m = Model(
            api_call_function.get(model.get("api_call_function")),
            model.get("model_name"),
            cipher_suite.decrypt(model.get("endpoint").encode()).decode(),
            cipher_suite.decrypt(model.get("api_key").encode()).decode(),
            inference_functions.get(model.get("inference_function")),
            model.get("content-type"),
            model.get("deployment_platform")
        )
        models += (m,)
    # Build the pipeline to call the models in order in the inference request
    for pipeline in result_json.get("pipelines"):
        CACHE["pipelines"][pipeline.get("pipeline_name")] = tuple([m for m in models if m.name in pipeline.get("models")])

    return result_json.get("pipelines")


async def data_factory(**kwargs):
    return {
        "input_data": kwargs,
    }


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
        # CACHE["endpoints"] = await fetch_json(NACHET_MODEL, "endpoints", "model_endpoints_metadata.json")
        CACHE["endpoints"] = await get_pipelines()

    except ServerError as e:
        if app.testing:
            print("Entering test mode")
            # Build test pipeline
            CACHE["endpoints"] = [
                        {
                            "pipeline_name": "test_pipeline",
                            "models": ["test_model1"]
                        }
                    ]
            # Built test model
            m = Model(
                model_module.request_inference_from_test,
                "test_model1",
                "http://localhost:8080/test_model1",
                "test_api_key",
                None,
                "application/json",
                "test_platform"
            )

            CACHE["pipelines"]["test_pipeline"] = (m,)
        else:
            print(e)
            raise ServerError(str(e))

    except Exception as e:
        print(e)
        raise ServerError("Failed to retrieve data from the repository")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
    