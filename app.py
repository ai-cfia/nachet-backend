import urllib.request
import json
import os
import base64
import ssl
import datetime
import numpy as np
from dotenv import load_dotenv
from quart import Quart, render_template, request, jsonify
from quart_cors import cors
from azure_storage_api import AzureStorageAPI


app = Quart(__name__)
app = cors(app, allow_origin="*")


@app.post("/del")
async def delete_dir():
    '''
    deletes a directory in the user's container
    '''
    data = await request.get_json()
    if 'container_name' in data and 'folder_name' in data:
        connection_string = os.getenv("CONNECTION_STRING")
        container_name = data['container_name']
        folder_name = data['folder_name']
        azure_storage_session = AzureStorageAPI(
            connection_string, container_name)
        container_client = await azure_storage_session.mount_container(create_container=False)
        if container_client:
            response = await azure_storage_session.delete_directory(folder_name)
            new_folder_list = await azure_storage_session.folder_list()
            return jsonify(new_folder_list)
    return False


@app.post("/dir")
async def list_dir():
    data = await request.get_json()
    if 'container_name' in data:
        connection_string = os.getenv("CONNECTION_STRING")
        container_name = data['container_name']
        azure_storage_session = AzureStorageAPI(
            connection_string, container_name)
        container_client = await azure_storage_session.mount_container(create_container=False)
        if container_client:
            response = await azure_storage_session.folder_list()
            return jsonify(response)
    return False


@app.post("/inf")
async def inference_request():
    data = await request.get_json()
    if 'image' in data and 'imageDims' in data and 'folder_name' in data and 'container_name' in data:
        if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
            ssl._create_default_https_context = ssl._create_unverified_context

        connection_string = os.getenv("CONNECTION_STRING")
        folder_name = data['folder_name']
        container_name = data['container_name']
        imageDims = data['imageDims']
        image_base64 = data['image']
        header, encoded_data = image_base64.split(',', 1)
        image_bytes = base64.b64decode(encoded_data)
        # initialize azure storage session object
        azure_storage_session = AzureStorageAPI(
            connection_string, container_name)
        # mount container
        container_client = await azure_storage_session.mount_container(create_container=True)
        if container_client:
            # generate hash value for image
            hash_value = await azure_storage_session.generate_hash(image_bytes)
            # upload image to azure storage
            blob_name = await azure_storage_session.upload_image(folder_name, image_bytes, hash_value)
            if blob_name:
                # get image from azure storage
                blob = await azure_storage_session.get_blob(blob_name)
                if blob:
                    image_bytes = base64.b64encode(blob).decode("utf8")
                    data = {
                        "input_data": {
                            "columns": [
                                "image"
                            ],
                            "index": [0],
                            "data": [image_bytes]
                        }
                    }

                    body = str.encode(json.dumps(data))
                    endpoint_url = os.getenv("ENDPOINT_URL")
                    endpoint_api_key = os.getenv("ENDPOINT_API_KEY")
                    headers = {'Content-Type': 'application/json',
                               'Authorization': ('Bearer ' + endpoint_api_key)}
                    req = urllib.request.Request(endpoint_url, body, headers)
                    try:
                        response = urllib.request.urlopen(req)
                        result = response.read()
                        result_json = json.loads(result.decode('utf-8'))
                        result_json_string = await azure_storage_session.process_inference_results(result_json, imageDims)
                        response = await azure_storage_session.upload_inference_results(folder_name, result_json_string, hash_value)
                        if response:
                            return jsonify(result_json)
                        else:
                            return jsonify([{"error": "Could not upload inference results to Azure Storage"}])

                    except urllib.error.HTTPError as error:
                        return jsonify([{"error": "The request failed with status code: " + str(error)}])
            else:
                return jsonify([{}])


@app.get("/ping")
async def ping():
    return "<html><body><h1>server is running</h1><body/><html/>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
