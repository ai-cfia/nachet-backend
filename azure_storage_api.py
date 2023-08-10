from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import hashlib
import os
import json
import uuid
import datetime
import uuid

'''
---- user-container based structure -----
- container name is user id
- whenever a new user is created, a new container is created with the user uuid
- inside the container, there are project folders (project name = project uuid)
- for each project folder, there is a json file with the project info and creation date, in the container
- inside the project folder, there is an image file and a json file with the image inference results
'''


class AzureStorageAPI(object):
    def __init__(self, connection_string, container_name):
        self.connection_string = connection_string
        self.container_name = container_name
        self.container_client = None

    async def mount_container(self, create_container=True):
        '''
        given a connection string and a container name, mounts the container and returns the container client as an object that can be used in other functions.
        if a specified container doesnt exist, it creates one with the provided uuid, if create_container is True
        '''
        try:
            blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string)
            # look for container
            self.container_client = blob_service_client.get_container_client(
                self.container_name)
            # if container doesnt exist, create one with provided uuid, if create_container is True
            if self.container_client.exists():
                return True
            elif create_container and not self.container_client.exists():
                self.container_client = blob_service_client.create_container(
                    self.container_name)
                return True
            else:
                return False
        except Exception as error:
            return False

    async def upload_image(self, folder_name, image, hash_value):
        '''
        upload the image to the specified folder within the user's container, if the specified folder doesnt exist, it creates it with a uuid
        '''
        try:
            folders_list = await self.folder_list()
            if folder_name not in folders_list:
                folder_uuid = uuid.uuid4()
                folder_data = {
                    "folder_name": folder_name,
                    "date_created": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                }
                image_name = "{}/{}.png".format(folder_uuid, hash_value)
                folder_name = "{}/{}.json".format(folder_uuid, folder_uuid)
                self.container_client.upload_blob(
                    image_name, image, overwrite=True)
                self.container_client.upload_blob(
                    folder_name, json.dumps(folder_data), overwrite=True)
                return image_name
            else:
                folder_uuid = await self.get_folder_uuid(folder_name)
                image_name = "{}/{}.png".format(folder_uuid, hash_value)
                self.container_client.upload_blob(
                    image_name, image, overwrite=True)
                return image_name
        except Exception as error:
            return False

    async def upload_inference_results(self, folder_name, result, hash_value):
        '''
        uploads the inference results json file to the specified folder in the users container 
        '''
        try:
            folder_uuid = await self.get_folder_uuid(folder_name)
            json_name = "{}/{}.json".format(folder_uuid, hash_value)
            self.container_client.upload_blob(
                json_name, result, overwrite=True)
            return True
        except Exception as error:
            return False

    async def get_blob(blob_name):
        '''
        gets the contents of a specified blob in the user's container
        '''
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob = blob_client.download_blob()
            blob_content = blob.readall()
            return blob_content
        except Exception as error:
            return False

    async def get_folder_uuid(self, folder_name):
        '''
        gets the uuid of a folder in the user's container given the folder name by
        iterating through the folder json files and extracting the name to match given folder name
        '''
        if self.container_client:
            folder_list = []
            blob_list = self.container_client.list_blobs()
            for blob in blob_list:
                if (blob.name.split(".")[-1] == "json" and blob.name.count("/") == 1 and blob.name.split("/")[0] == blob.name.split("/")[1].split(".")[0]):
                    folder_json = await self.get_blob(blob.name)
                    folder_json = json.loads(folder_json)
                    if folder_json['folder_name'] == folder_name:
                        return blob.name.split(".")[0].split("/")[-1]
        else:
            return False

    async def delete_directory(self, folder_name):
        '''
        deletes a specified folder in the user's container given the folder name
        '''
        if self.container_client:
            folder_uuid = await self.get_folder_uuid(folder_name)
            if folder_uuid:
                blob_list = self.container_client.list_blobs()
                for blob in blob_list:
                    if blob.name.split("/")[0] == folder_uuid:
                        self.container_client.delete_blob(blob.name)
                return True
        return False

    async def folder_list(self):
        '''
        returns a list of folder names in the user's container
        '''
        if self.container_client:
            folder_list = []
            blob_list = self.container_client.list_blobs()
            for blob in blob_list:
                if (blob.name.split(".")[-1] == "json" and blob.name.count("/") == 1 and blob.name.split("/")[0] == blob.name.split("/")[1].split(".")[0]):
                    folder_blob = await self.get_blob(blob.name)
                    folder_json = json.loads(folder_blob)
                    folder_list.append(folder_json['folder_name'])
            folder_list.sort()
            return list(set(folder_list))
        return []

    async def generate_hash(image):
        '''
        generates a hash value for the image to be used as the image name in the container
        '''
        try:
            hash = hashlib.sha256(image).hexdigest()
            return hash
        except Exception as error:
            return False

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
            box["box"]["bottomX"] = int(
                np.clip(box["box"]["bottomX"] * imageDims[0], 5, imageDims[0] - 5))
            box["box"]["bottomY"] = int(
                np.clip(box["box"]["bottomY"] * imageDims[1], 5, imageDims[1] - 5))
            box["box"]["topX"] = int(
                np.clip(box["box"]["topX"] * imageDims[0], 5, imageDims[0] - 5))
            box["box"]["topY"] = int(
                np.clip(box["box"]["topY"] * imageDims[1], 5, imageDims[1] - 5))

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
        data[0]["totalBoxes"] = sum(
            1 for box in data[0]["boxes"] if box["overlapping"] == False)

        result_json_string = json.dumps(data)
        return result_json_string
