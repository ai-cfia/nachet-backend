import urllib.request
import json
import os
import base64
import re
from dotenv import load_dotenv
from quart import Quart, request, jsonify
from quart_cors import cors
import azure_storage.azure_storage_api as azure_storage_api
import model_inference.inference as inference
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

endpoint_url_regex = r"^https://.*\/score$"
endpoint_url = os.getenv("NACHET_MODEL_ENDPOINT_REST_URL")

endpoint_api_key = os.getenv("NACHET_MODEL_ENDPOINT_ACCESS_KEY")

NACHET_DATA = os.getenv("NACHET_DATA")
NACHET_MODEL = os.getenv("NACHET_MODEL")

CACHE = {
    'seeds': None,
    'endpoints': None
}

# Check: do environment variables exist?
if connection_string is None:
    raise ServerError("Missing environment variable: NACHET_AZURE_STORAGE_CONNECTION_STRING")

if endpoint_url is None:
    raise ServerError("Missing environment variable: NACHET_MODEL_ENDPOINT_REST_URL")

if endpoint_api_key is None:
    raise ServerError("Missing environment variables: NACHET_MODEL_ENDPOINT_ACCESS_KEY")

# Check: are environment variables correct? 
if not bool(re.match(connection_string_regex, connection_string)):
    raise ServerError("Incorrect environment variable: NACHET_AZURE_STORAGE_CONNECTION_STRING")

if not bool(re.match(endpoint_url_regex, endpoint_url)):
    raise ServerError("Incorrect environment variable: NACHET_MODEL_ENDPOINT_ACCESS_KEY")

app = Quart(__name__)
app = cors(app, allow_origin="*", allow_methods=["GET", "POST", "OPTIONS"])

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
    try:
        data = await request.get_json()
        model_name = data.get("model_name", "default_model")  # Default to 'default_model' if not provided
        connection_string: str = os.environ["NACHET_AZURE_STORAGE_CONNECTION_STRING"]
        folder_name = data["folder_name"]
        container_name = data["container_name"]
        imageDims = data["imageDims"]
        image_base64 = data["image"]
        if not (folder_name and container_name and imageDims and image_base64):
            return jsonify(["missing request arguments"]), 400

        header, encoded_data = image_base64.split(",", 1)
        image_bytes = base64.b64decode(encoded_data)
        container_client = await azure_storage_api.mount_container(
            connection_string, container_name, create_container=True
        )
        hash_value = await azure_storage_api.generate_hash(image_bytes)
        blob_name = await azure_storage_api.upload_image(
            container_client, folder_name, image_bytes, hash_value
        )
        blob = await azure_storage_api.get_blob(container_client, blob_name)
        image_bytes = base64.b64encode(blob).decode("utf8")
        
        # Model function mapping
        model_mapping = {
            "Seed Classification": inference.process_inference_results,
            #"another_model": inference.another_model_function,  # Example for another model
            # Add more models as needed
        }
        
        # Prepare the data for the processing function or model endpoint
        input_data = {
            "input_data": {
                "columns": ["image"],
                "index": [0],
                "data": [image_bytes],
            }
        }
        
        # Select the appropriate model function
        model_function = model_mapping.get(model_name)
        if not model_function:
            return jsonify([f"Model {model_name} not found"]), 400

        # Encode the data as json to be sent to the model endpoint or processing function
        body = str.encode(json.dumps(input_data))
        
        # Dynamic selection of model endpoint URL and API key
        endpoint_url = os.getenv(f"{model_name.upper()}_MODEL_ENDPOINT_REST_URL", os.getenv("NACHET_MODEL_ENDPOINT_REST_URL"))
        endpoint_api_key = os.getenv(f"{model_name.upper()}_MODEL_ENDPOINT_ACCESS_KEY", os.getenv("NACHET_MODEL_ENDPOINT_ACCESS_KEY"))

        headers = {
            "Content-Type": "application/json",
            "Authorization": ("Bearer " + endpoint_api_key),
        }

        # Send the request to the model endpoint or call the local processing function
        req = urllib.request.Request(endpoint_url, body, headers)
        try:
            response = urllib.request.urlopen(req)
            result = response.read()
            result_json = json.loads(result.decode("utf-8"))
            
            data_for_inference = [{"boxes": result_json}] if model_name != "Seed Classification" else result_json

            # Perform inference using the selected model
            processed_result_json = await model_function(
                data_for_inference, imageDims  # Pass the necessary parameters
            )
            
        except urllib.error.HTTPError as error:
            print(error)
            return jsonify(["Endpoint cannot be reached: " + str(error.code)]), 400

        # Upload the inference results to the user's container as an async task
        result_json_string = json.dumps(processed_result_json)
        app.add_background_task(
            azure_storage_api.upload_inference_result,
            container_client,
            folder_name,
            result_json_string,
            hash_value,
        )

        # Return the inference results to the client
        return jsonify(processed_result_json), 200

    except InferenceRequestError as error:
        print(error)
        return jsonify(["InferenceRequestError: " + str(error)]), 400
    except Exception as e:  # Catch any other exception
        print(f"Unexpected error: {e}")
        return jsonify(["Unexpected error occurred"]), 500

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

    
async def fetch_json(repo_URL, key, file_path):
    """
    Fetches JSON document from a GitHub repository and caches it
    """
    try:
        json_url = os.path.join(repo_URL, file_path)
        with urllib.request.urlopen(json_url) as response:
            result = response.read()
            result_json = json.loads(result.decode("utf-8"))
            CACHE[key] = result_json
    except urllib.error.HTTPError as error:
        return jsonify({"error": f"Failed to retrieve the JSON. \
                        HTTP Status Code: {error.code}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.before_serving
async def before_serving():
    await fetch_json(NACHET_DATA, 'seeds', "seeds/all.json")
    await fetch_json(NACHET_MODEL, 'endpoints', 'model_endpoints_metadata.json')


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
    
