from unittest.main import MODULE_EXAMPLES
import urllib.request
import json
import os
import base64
import re
import io
import magic
import time
import warnings
import tempfile

from PIL import Image
from datetime import date
from dotenv import load_dotenv
from quart import Quart, request, jsonify
from quart_cors import cors
from collections import namedtuple
from cryptography.fernet import Fernet

load_dotenv()

from azure.core.exceptions import ResourceNotFoundError, ServiceResponseError
import model.inference as inference
from model import request_function
import storage.datastore_storage_api as datastore
from datastore import azure_storage
from storage import azure_storage_api as old_azure_storage_api

class APIErrors(Exception):
    pass


class DeleteDirectoryRequestError(APIErrors):
    pass


class ListDirectoriesRequestError(APIErrors):
    pass


class InferenceRequestError(APIErrors):
    pass


class CreateDirectoryRequestError(APIErrors):
    pass


class ServerError(APIErrors):
    pass


class ImageValidationError(APIErrors):
    pass


class ValidateEnvVariablesError(APIErrors):
    pass


class EmailNotSendError(APIErrors):
    pass


class EmptyPictureSetError(APIErrors):
    pass


class APIWarnings(UserWarning):
    pass


class ImageWarning(APIWarnings):
    pass


class MaxContentLengthWarning(APIWarnings):
    pass


connection_string_regex = r"^DefaultEndpointsProtocol=https?;.*;FileEndpoint=https://[a-zA-Z0-9]+\.file\.core\.windows\.net/;$"
pipeline_version_regex = r"\d.\d.\d"

CONNECTION_STRING = os.getenv("NACHET_AZURE_STORAGE_CONNECTION_STRING")

FERNET_KEY = os.getenv("NACHET_BLOB_PIPELINE_DECRYPTION_KEY")
PIPELINE_VERSION = os.getenv("NACHET_BLOB_PIPELINE_VERSION")
PIPELINE_BLOB_NAME = os.getenv("NACHET_BLOB_PIPELINE_NAME")

NACHET_DATA = os.getenv("NACHET_DATA")

try:
    VALID_EXTENSION = json.loads(os.getenv("NACHET_VALID_EXTENSION"))
    VALID_DIMENSION = json.loads(os.getenv("NACHET_VALID_DIMENSION"))
except (TypeError, json.decoder.JSONDecodeError):
    # For testing
    VALID_DIMENSION = {"width": 1920, "height": 1080}
    VALID_EXTENSION = {"jpeg", "jpg", "png", "gif", "bmp", "tiff", "webp"}
    warnings.warn(
        f"""
        NACHET_VALID_EXTENSION or NACHET_VALID_DIMENSION is not set,
        using default values: {", ".join(list(VALID_EXTENSION))} and dimension: {tuple(VALID_DIMENSION.values())}
        """,
        ImageWarning
    )

try:
    MAX_CONTENT_LENGTH_MEGABYTES = int(os.getenv("NACHET_MAX_CONTENT_LENGTH"))
except (TypeError, ValueError):
    MAX_CONTENT_LENGTH_MEGABYTES = 16
    warnings.warn(
        f"NACHET_MAX_CONTENT_LENGTH not set, using default value of {MAX_CONTENT_LENGTH_MEGABYTES}",
        MaxContentLengthWarning
    )


Model = namedtuple(
    'Model',
    [
        'request_function',
        'name',
        'version',
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
    "validators": []
}

app = Quart(__name__)
app = cors(app, allow_origin="*", allow_methods=["GET", "POST", "OPTIONS"])
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH_MEGABYTES * 1024 * 1024


@app.before_serving
async def before_serving():
    try:
        # Check: do environment variables exist?
        if CONNECTION_STRING is None:
            raise ServerError("Missing environment variable: NACHET_AZURE_STORAGE_CONNECTION_STRING")

        if FERNET_KEY is None:
            raise ServerError("Missing environment variable: FERNET_KEY")

        if PIPELINE_VERSION is None:
            raise ServerError("Missing environment variable: PIPELINE_VERSION")

        if PIPELINE_BLOB_NAME is None:
            raise ServerError("Missing environment variable: PIPELINE_BLOB_NAME")

        if NACHET_DATA is None:
            raise ServerError("Missing environment variable: NACHET_DATA")

        # Check: are environment variables correct?
        if not bool(re.match(connection_string_regex, CONNECTION_STRING)):
            raise ServerError("Incorrect environment variable: NACHET_AZURE_STORAGE_CONNECTION_STRING")

        if not bool(re.match(pipeline_version_regex, PIPELINE_VERSION)):
            raise ServerError("Incorrect environment variable: PIPELINE_VERSION")

        # Store the seeds names and ml structure in CACHE
        CACHE["seeds"] = datastore.get_all_seeds_names() 
        seeds = datastore.get_all_seeds()
        print(jsonify(seeds))
        CACHE["endpoints"] = await get_pipelines()
        
        print(
            f"""Server start with current configuration:\n
                date: {date.today()}
                file version of pipelines: {PIPELINE_VERSION}
                pipelines: {[pipeline for pipeline in CACHE["pipelines"].keys()]}\n
            """
        ) #TODO Transform into logging

    except (ServerError, inference.ModelAPIErrors) as e:
        print(e)
        raise


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
            container_client = await azure_storage.mount_container(
                CONNECTION_STRING, container_name, create_container=True
            )
            if container_client:
                folder_uuid = await azure_storage.get_folder_uuid(
                    container_client, folder_name
                )
                if folder_uuid:
                    blob_list = container_client.list_blobs()
                    for blob in blob_list:
                        if blob.name.split("/")[0] == folder_uuid:
                            container_client.delete_blob(blob.name)
                    return jsonify([True]), 200
                else:
                    raise DeleteDirectoryRequestError("directory does not exist")
            else:
                raise DeleteDirectoryRequestError("failed to mount container")
        else:
            raise DeleteDirectoryRequestError("missing container or directory name")

    except (KeyError, TypeError, azure_storage.MountContainerError, ResourceNotFoundError, DeleteDirectoryRequestError, ServiceResponseError) as error:
        print(error)
        return jsonify([f"DeleteDirectoryRequestError: {str(error)}"]), 400


@app.post("/dir")
async def list_directories():
    """
    lists all directories in the user's container
    """
    try:
        data = await request.get_json()
        container_name = data["container_name"]
        if container_name:
            container_client = await azure_storage.mount_container(
                CONNECTION_STRING, container_name, create_container=True
            )
            response = await azure_storage.get_directories(container_client)
            return jsonify(response), 200
        else:
            raise ListDirectoriesRequestError("Missing container name")

    except (KeyError, TypeError, ListDirectoriesRequestError, azure_storage.MountContainerError) as error:
        print(error)
        return jsonify([f"ListDirectoriesRequestError: {str(error)}"]), 400


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
            container_client = await azure_storage.mount_container(
                CONNECTION_STRING, container_name, create_container=True
            )
            response = await azure_storage.create_folder(
                container_client, folder_name
            )
            if response:
                return jsonify([True]), 200
            else:
                raise CreateDirectoryRequestError("directory already exists")
        else:
            raise CreateDirectoryRequestError("missing container or directory name")

    except (KeyError, TypeError, CreateDirectoryRequestError, azure_storage.MountContainerError) as error:
        print(error)
        return jsonify([f"CreateDirectoryRequestError: {str(error)}"]), 400


@app.post("/image-validation")
async def image_validation():
    """
    Validates an image based on its extension, header, size, and resizability.

    Returns:
        A JSON response containing a validator hash.

    Raises:
        ImageValidationError: If the image fails any of the validation checks.
    """
    try:

        data = await request.get_json()
        image_base64 = data["image"]

        header, encoded_image = image_base64.split(",", 1)
        image_bytes = base64.b64decode(encoded_image)

        image = Image.open(io.BytesIO(image_bytes))

        # size check
        if image.size[0] > VALID_DIMENSION["width"] and image.size[1] > VALID_DIMENSION["height"]:
            raise ImageValidationError(f"invalid file size: {image.size[0]}x{image.size[1]}")

        # resizable check
        try:
            size = (100,150)
            image.thumbnail(size)
        except IOError:
            raise ImageValidationError("invalid file not resizable")

        magic_header = magic.from_buffer(image_bytes, mime=True)
        image_extension = magic_header.split("/")[1]

        # extension check
        if image_extension not in VALID_EXTENSION:
           raise ImageValidationError(f"invalid file extension: {image_extension}")

        expected_header = f"data:image/{image_extension};base64"

        # header check
        if header.lower() != expected_header:
            raise ImageValidationError(f"invalid file header: {header}")

        validator = await azure_storage.generate_hash(image_bytes)
        CACHE['validators'].append(validator)

        return jsonify([validator]), 200

    except (KeyError, TypeError, ValueError, ImageValidationError) as error:
        print(error)
        return jsonify([f"ImageValidationError: {str(error)}"]), 400


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
        validator = data.get("validator")
        folder_name = data["folder_name"]
        container_name = data["container_name"]
        imageDims = data["imageDims"]
        image_base64 = data["image"]
        #user_id = data.get["user_id"]
        email = "example@gmail.com"
        
        area_ratio = data.get("area_ratio", 0.5)
        color_format = data.get("color_format", "hex")

        print(f"Requested by user: {container_name}") # TODO: Transform into logging
        pipelines_endpoints = CACHE.get("pipelines")
        validators = CACHE.get("validators")

        if not (folder_name and container_name and imageDims and image_base64):
            raise InferenceRequestError(
                "missing request arguments: either folder_name, container_name, imageDims or image is missing")

        if not pipelines_endpoints.get(pipeline_name):
            raise InferenceRequestError(f"model {pipeline_name} not found")

        _, encoded_data = image_base64.split(",", 1)

        if validator not in validators:
            warnings.warn("this picture was not validate", ImageWarning)
            # TODO: implement logic when frontend start returning validators

        # Keep track of every output given by the models
        # TODO: add it to CACHE variable
        cache_json_result = [encoded_data]
        image_bytes = base64.b64decode(encoded_data)

        container_client = await azure_storage.mount_container(
            CONNECTION_STRING, container_name, create_container=True
        )
        
        # Open db connection
        connection = datastore.get_connection()
        cursor = datastore.get_cursor(connection)
        
        user = await datastore.validate_user(cursor, email, CONNECTION_STRING)

        image_hash_value = await azure_storage.generate_hash(image_bytes)
        picture_id = await datastore.get_picture_id(
            cursor, user.id, image_hash_value, container_client
        )
        
        pipeline = pipelines_endpoints.get(pipeline_name)

        for idx, model in enumerate(pipeline):
            print(f"Entering {model.name.upper()} model") # TODO: Transform into logging
            result_json = await model.request_function(model, cache_json_result[idx])
            cache_json_result.append(result_json)

        print("End of inference request") # TODO: Transform into logging
        print("Process results") # TODO: Transform into logging

        processed_result_json = await inference.process_inference_results(
            cache_json_result[-1], imageDims, area_ratio, color_format
        )

        result_json_string = await record_model(pipeline, processed_result_json)

        # upload the inference results to the user's container as async task
        app.add_background_task(
            azure_storage.upload_inference_result,
            container_client,
            folder_name,
            result_json_string,
            image_hash_value,
        )
        saved_result_json = await datastore.save_inference_result(cursor, user.id, processed_result_json[0], picture_id, pipeline_name, 1)
        
        datastore.end_query(connection, cursor)
        
        # return the inference results to the client
        print(f"Took: {'{:10.4f}'.format(time.perf_counter() - seconds)} seconds") # TODO: Transform into logging
        return jsonify(saved_result_json), 200

    except (inference.ModelAPIErrors, KeyError, TypeError, ValueError, InferenceRequestError, azure_storage.MountContainerError) as error:
        print(error)
        return jsonify(["InferenceRequestError: " + error.args[0]]), 400

@app.get("/picture-form")
async def get_picture_form_info():
    """
    Retrieves the names of seeds from the database and returns them as a JSON
    response.

    Returns:
        A JSON response containing the names of seeds.

    Raises:
        APIErrors: If there is an error while retrieving the seeds names from
        the database.
    """
    try:
        seeds_names = datastore.get_all_seeds_names()
        return jsonify(seeds_names), 200
    except datastore.DatastoreError as error:
        return jsonify([error.args[0]]), 400

@app.put("/upload-pictures")
async def picture_batch_import():
    """
    This function handles the batch import of pictures.

    It performs the following steps:
    1. Uploads and chunks the file.
    2. Reconstructs the file and extracts data.
    3. Validates and uploads the data.

    Returns:
    - If successful, returns a JSON response with the picture ID and a status code of 200.
    - If an error occurs, returns a JSON response with the error message and a status code of 400.
    """
    try:
        temp_files = await upload_and_chunk_file(request)
        email, picture_set, data = reconstruct_file_and_extract_data(temp_files)
        picture_id = validate_and_upload_data(email, picture_set, data)
        return jsonify([picture_id]), 200
    except APIErrors as error:
        return jsonify([error.args[0]]), 400

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
    except urllib.error.HTTPError as e:
        return jsonify(
            {f"An error happend when reloading the seed data: {e.args[0]}"}), 500


@app.get("/model-endpoints-metadata")
async def get_model_endpoints_metadata():
    """
    Returns JSON containing the deployed endpoints' metadata
    """
    if CACHE['endpoints']:
        return jsonify(CACHE['endpoints']), 200
    else:
        return jsonify("Error retrieving model endpoints metadata.", 404)


@app.get("/seeds")
async def get_seeds():
    """
    Returns JSON containing the model seeds metadata
    """
    seeds = await datastore.get_all_seeds()
    print(jsonify(seeds))
    if seeds :
        return jsonify(seeds), 200
    else:
        return jsonify("Error retrieving seeds", 404)


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
        1,
        "http://localhost:8080/test_model1",
        "test_api_key",
        "application/json",
        "test_platform"
    )

    CACHE["pipelines"]["test_pipeline"] = (m,)

    return CACHE["endpoints"], 200


async def record_model(pipeline: namedtuple, result: list):
    new_entry = [{"name": model.name, "version": model.version} for model in pipeline]
    result[0]["models"] = new_entry
    return json.dumps(result, indent=4)

async def upload_and_chunk_file(request):
    """
    Uploads a file and chunks it into smaller parts.

    Args:
        request: The request object containing the file to be uploaded.

    Returns:
        A list of file paths representing the chunks of the uploaded file.
    """
    temp_dir = tempfile.TemporaryDirectory()
    
    upload_stream = await request.stream()    
    chunk_filename = os.path.join(temp_dir.name, f"chunk_{len(os.listdir(temp_dir.name))}")
    with open(chunk_filename, "wb") as chunk_file:
        async for chunk in upload_stream:
            chunk_file.write(chunk)

    return [os.path.join(temp_dir.name, f) for f in os.listdir(temp_dir.name)]

def reconstruct_file_and_extract_data(temp_files):
    """
    Reconstructs a file from multiple chunks and extracts data from it.

    Args:
        temp_files (list): A list of file paths to the temporary chunk files.

    Returns:
        tuple: A tuple containing the extracted email, picture_set, and the original data.
    """
    full_file = b''
    for chunk_filename in temp_files:
        with open(chunk_filename, "rb") as chunk_file:
            full_file += chunk_file.read()
    data = json.loads(full_file)
    email = data.get("email")
    picture_set = data.get("picture_set")
    return email, picture_set, data

def validate_and_upload_data(email, picture_set, data):
    """
    Validates the input parameters and uploads the picture set data to the database.

    Args:
        email (str): The user's email address.
        picture_set (list): The list of pictures in the picture set.
        data (dict): Additional data for the picture set.

    Returns:
        int: The ID of the uploaded picture set.

    Raises:
        EmailNotSendError: If the user email is not provided.
        EmptyPictureSetError: If no picture set is provided.
    """
    if email is None:
        raise EmailNotSendError("the user email is not provided")
    if not picture_set:
        raise EmptyPictureSetError("no picture set provided")
    user_id = datastore.validate_user(email)
    picture_id = datastore.upload_picture_set(user_id=user_id, **data)
    return picture_id

async def fetch_json(repo_URL, key, file_path):
    """
    Fetches JSON document from a GitHub repository.

    Parameters:
    - repo_URL (str): The URL of the GitHub repository.
    - key (str): The key to identify the JSON document.
    - file_path (str): The path to the JSON document in the repository.

    Returns:
    - dict: The JSON document as a Python dictionary.
    """
    if key != "endpoints":
        json_url = os.path.join(repo_URL, file_path)
        with urllib.request.urlopen(json_url) as response:
            result = response.read()
            result_json = json.loads(result.decode("utf-8"))
        return result_json


async def get_pipelines(cipher_suite=Fernet(FERNET_KEY)):
    """
    Retrieves the pipelines from the Azure storage API.

    Returns:
    - list: A list of dictionaries representing the pipelines.
    """
    result_json = await datastore.get_pipelines()

    models = ()
    for model in result_json.get("models"):
        m = Model(
            request_function.get(model.get("model_name")),
            model.get("model_name"),
            model.get("version"),
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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
