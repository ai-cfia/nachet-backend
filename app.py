import urllib.request
import json
import os
import base64
import ssl
import datetime
from dotenv import load_dotenv
from quart import Quart, render_template, request, jsonify
from quart_cors import cors
import azure_storage_api
import inference
from custom_exceptions import *

app = Quart(__name__)
app = cors(app, allow_origin="*")

@app.post("/del")
async def delete_dir():
    '''
    deletes a directory in the user's container
    '''
    try:

        data = await request.get_json()
        connection_string = os.getenv("CONNECTION_STRING")
        if data['container_name'] and data['folder_name']:
            container_name = data['container_name']
            folder_name = data['folder_name']
            container_client = await azure_storage_api.mount_container(connection_string, container_name, create_container=False)
            folder_uuid = await azure_storage_api.get_folder_uuid(folder_name, container_client)
            if folder_uuid:
                blob_list = container_client.list_blobs()
                for blob in blob_list:
                    if blob.name.split("/")[0] == folder_uuid:
                        container_client.delete_blob(blob.name)
                return jsonify([True])
        else:
            raise DeleteDirectoryRequestError("Invalid container name or folder name")

    except DeleteDirectoryRequestError as error:
        print(error)
        return jsonify([])


@app.post("/dir")
async def list_dir():
    '''
    lists all directories in the user's container
    '''
    try:

        data = await request.get_json()
        connection_string = os.getenv("CONNECTION_STRING")
        if data['container_name']:
            container_name = data['container_name']
            container_client = await azure_storage_api.mount_container(connection_string, container_name, create_container=False)
            response = await azure_storage_api.folder_list(container_client)
            return jsonify(response)
        else:
            raise ListDirectoryRequestError("Invalid container name")

    except ListDirectoryRequestError as error:
        print(error)
        return jsonify([])


@app.post("/inf")
async def inference():
    '''
    performs inference on an image, and returns the results. 
    The image and inference results uploaded to a folder in the user's container.
    '''
    try:

        data = await request.get_json()
        if data['image'] and data['imageDims'] and data['folder_name'] and data['container_name']:
            if not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
                ssl._create_default_https_context = ssl._create_unverified_context
            connection_string = os.getenv("CONNECTION_STRING")
            folder_name = data['folder_name']
            container_name = data['container_name']
            imageDims = data['imageDims']
            image_base64 = data['image']
            header, encoded_data = image_base64.split(',', 1)
            image_bytes = base64.b64decode(encoded_data)
            container_client = await azure_storage_api.mount_container(connection_string, container_name, create_container=True)
            hash_value = await azure_storage_api.generate_hash(image_bytes)
            blob_name = await azure_storage_api.upload_image(folder_name, image_bytes, container_client, hash_value)
            blob = await azure_storage_api.get_blob(blob_name, container_client)
            image_bytes = base64.b64encode(blob).decode("utf8")
            data =  {
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
            headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ endpoint_api_key)}
            req = urllib.request.Request(endpoint_url, body, headers)
            try:

                response = urllib.request.urlopen(req)
                result = response.read()
                result_json = json.loads(result.decode('utf-8'))
                processed_result_json = await inference.process_inference_results(result_json, imageDims)
                result_json_string = json.dumps(processed_result_json)
                azure_storage_api.upload_inference_result(folder_name, result_json_string, container_client, hash_value);
                return jsonify(result_json_string)
                
            except urllib.error.HTTPError as error:
                print("The request failed with status code: " + str(error.code))
                return jsonify([])
                
    except InferenceRequestError as error:
        print(error)
        return jsonify([])

@app.get("/ping")
async def ping():
    return "<html><body><h1>server is running</h1><body/><html/>"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
