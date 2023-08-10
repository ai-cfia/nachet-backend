import urllib.request
import json
import os, uuid
import base64
import ssl
import hashlib
import datetime
import numpy as np
from dotenv import load_dotenv
from quart import Quart, render_template, request, jsonify
from quart_cors import cors
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

'''
---- user-container based structure -----
- container name is user id
- whenever a new user is created, a new container is created with the user uuid
- inside the container, there are project folders (project name = project uuid)
- for each project folder, there is a json file with the project info and creation date, in the container
- inside the project folder, there is an image file and a json file with the image inference results
'''

app = Quart(__name__)
app = cors(app, allow_origin="*")

async def generate_hash(image):
    '''
    generates a hash value for the image to be used as the image name in the container
    '''
    try:
        hash = hashlib.sha256(image).hexdigest()
        return hash
    except Exception as error:
        return False

async def mount_container(connection_string, container_name, create_container=True):
    '''
    given a connection string and a container name, mounts the container and returns the container client as an object that can be used in other functions.
    if a specified container doesnt exist, it creates one with the provided uuid, if create_container is True
    '''
    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        # look for container
        container_client = blob_service_client.get_container_client(container_name)
        # if container doesnt exist, create one with provided uuid, if create_container is True
        if container_client.exists():
            return container_client
        elif create_container and not container_client.exists():
            container_client = blob_service_client.create_container(container_name)
            return container_client
        else:
            return False
    except Exception as error:
        return False

async def get_blob(blob_name, container_client):
    '''
    gets the contents of a specified blob in the user's container
    '''
    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob = blob_client.download_blob()
        blob_content = blob.readall()
        return blob_content
    except Exception as error:
        return False

async def upload_image(folder_name, image, container_client, hash_value):
    '''
    uploads the image to the specified folder within the user's container, if the specified folder doesnt exist, it creates it with a uuid
    '''
    try:
        folders_list = await folder_list(container_client)
        if folder_name not in folders_list:
            folder_uuid = uuid.uuid4()
            folder_data = {
                "folder_name": folder_name,
                "date_created": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            }
            image_name = "{}/{}.png".format(folder_uuid, hash_value)
            folder_name = "{}/{}.json".format(folder_uuid, folder_uuid)
            container_client.upload_blob(image_name, image, overwrite=True)
            container_client.upload_blob(folder_name, json.dumps(folder_data), overwrite=True)
            return image_name
        else:
            folder_uuid = await get_folder_uuid(folder_name, container_client)
            blob_name = "{}/{}.png".format(folder_uuid, hash_value)
            container_client.upload_blob(blob_name, image, overwrite=True)
            return blob_name
    except Exception as error:
        return False

async def upload_inference_results(folder_name, result, container_client, hash_value):
    '''
    uploads the inference results json file to the specified folder in the users container 
    '''
    try:
        folder_uuid = await get_folder_uuid(folder_name, container_client)
        json_name = "{}/{}.json".format(folder_uuid, hash_value)
        container_client.upload_blob(json_name, result, overwrite=True)
        return True
    except Exception as error:
        return False

async def get_folder_uuid(folder_name, container_client):
    '''
    gets the uuid of a folder in the user's container given the folder name by
    iterating through the folder json files and extracting the name to match given folder name
    '''
    if container_client:
        folder_list = []
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            if (blob.name.split(".")[-1] == "json" and blob.name.count("/") == 1 and blob.name.split("/")[0] == blob.name.split("/")[1].split(".")[0]):
                folder_json = await get_blob(blob.name, container_client)
                folder_json = json.loads(folder_json)
                if folder_json['folder_name'] == folder_name:
                    return blob.name.split(".")[0].split("/")[-1]
    else:
        return False

async def folder_list(container_client):
    '''
    returns a list of folder names in the user's container
    '''
    if container_client:
        folder_list = []
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            if (blob.name.split(".")[-1] == "json" and blob.name.count("/") == 1 and blob.name.split("/")[0] == blob.name.split("/")[1].split(".")[0]):
                folder_blob = await get_blob(blob.name, container_client)
                folder_json = json.loads(folder_blob)
                folder_list.append(folder_json['folder_name'])
        folder_list.sort()
        return list(set(folder_list))
    return []

async def process_inference_results(data, imageDims):
    '''
    processes the inference results to add additional attributes to the inference results that are used in the frontend
    '''
    data = data

    for i, box in enumerate(data[0]["boxes"]):
        # set default overlapping attribute to false for each box
        data[0]["boxes"][i]["overlapping"] = False
        # set default overlapping key to None for each box
        data[0]["boxes"][i]["overlappingIndex"] = -1
        box["box"]["bottomX"] = int(np.clip(box["box"]["bottomX"] * imageDims[0], 5, imageDims[0] - 5))
        box["box"]["bottomY"] = int(np.clip(box["box"]["bottomY"] * imageDims[1], 5, imageDims[1] - 5))
        box["box"]["topX"] = int(np.clip(box["box"]["topX"] * imageDims[0], 5, imageDims[0] - 5))
        box["box"]["topY"] = int(np.clip(box["box"]["topY"] * imageDims[1], 5, imageDims[1] - 5))

    # check if there any overlapping boxes, if so, put the lower scoer box in the overlapping key
    for i, box in enumerate(data[0]["boxes"]):
        for j, box2 in enumerate(data[0]["boxes"]):
            if i != j:
                if (box["box"]["bottomX"] >= box2["box"]["topX"] and box["box"]["bottomY"] >= box2["box"]["topY"] and box["box"]["topX"] <= box2["box"]["bottomX"] and box["box"]["topY"] <= box2["box"]["bottomY"]):
                    if box["score"] >= box2["score"]:
                        data[0]["boxes"][j]["overlapping"] = True
                        data[0]["boxes"][j]["overlappingIndex"] = i + 1
                        box2["box"]["bottomX"] = box["box"]["bottomX"]
                        box2["box"]["bottomY"] = box["box"]["bottomY"]
                        box2["box"]["topX"] = box["box"]["topX"]
                        box2["box"]["topY"] = box["box"]["topY"]
                    else:
                        data[0]["boxes"][i]["overlapping"] = True
                        data[0]["boxes"][i]["overlappingIndex"] = j + 1
                        box["box"]["bottomX"] = box2["box"]["bottomX"]
                        box["box"]["bottomY"] = box2["box"]["bottomY"]
                        box["box"]["topX"] = box2["box"]["topX"]
                        box["box"]["topY"] = box2["box"]["topY"]

    labelOccurrence = {}
    for i, box in enumerate(data[0]["boxes"]):
        if (box["overlapping"] == False):
            if box["label"] not in labelOccurrence:
                labelOccurrence[box["label"]] = 1
            else:
                labelOccurrence[box["label"]] += 1

    data[0]["labelOccurrence"] = labelOccurrence
    # add totalBoxes attribute to the inference results
    data[0]["totalBoxes"] = sum(1 for box in data[0]["boxes"] if box["overlapping"] == False)

    result_json_string = json.dumps(data)
    return result_json_string

@app.post("/del")
async def delete_dir():
    '''
    deletes a directory in the user's container
    '''
    data = await request.get_json()
    connection_string = os.getenv("CONNECTION_STRING")
    if 'container_name' in data and 'folder_name' in data:
        container_name = data['container_name']
        folder_name = data['folder_name']
        container_client = await mount_container(connection_string, container_name, create_container=False)
        if container_client:
            folder_uuid = await get_folder_uuid(folder_name, container_client)
            if folder_uuid:
                blob_list = container_client.list_blobs()
                for blob in blob_list:
                    if blob.name.split("/")[0] == folder_uuid:
                        container_client.delete_blob(blob.name)

                return jsonify([True])
    
    return jsonify([])

@app.post("/dir")
async def list_dir():
    data = await request.get_json()
    connection_string = os.getenv("CONNECTION_STRING")
    if 'container_name' in data:
        container_name = data['container_name']
        container_client = await mount_container(connection_string, container_name, create_container=False)
        if container_client:
            response = await folder_list(container_client)
            if response:
                return jsonify(response)
    return jsonify([])

@app.post("/inf")
async def inf():
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
        # mount container
        container_client = await mount_container(connection_string, container_name, create_container=True)
        if container_client:
            # generate hash value for image
            hash_value = await generate_hash(image_bytes)
            # upload image to azure storage
            blob_name = await upload_image(folder_name, image_bytes, container_client, hash_value)
            # get image from azure storage
            blob = await get_blob(blob_name, container_client)
            if blob:
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
                    result_json_string = await process_inference_results(result_json, imageDims)
                    response = await upload_inference_results(folder_name, result_json_string, container_client, hash_value);

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