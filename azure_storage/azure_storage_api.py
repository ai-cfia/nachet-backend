import json
import uuid
import hashlib
import datetime
from azure.storage.blob import BlobServiceClient
from custom_exceptions import (
    ConnectionStringError,
    MountContainerError,
    GetBlobError,
    UploadImageError,
    UploadInferenceResultError,
    GetFolderUUIDError,
    FolderListError,
    GenerateHashError,
    CreateDirectoryError,
)

"""
---- user-container based structure -----
- container name is user id
- whenever a new user is created, a new container is created with the user uuid
- inside the container, there are project folders (project name = project uuid)
- for each project folder, there is a json file with the project info and creation
date, in the container
- inside the project folder, there is an image file and a json file with
the image inference results
"""


async def generate_hash(image):
    """
    generates a hash value for the image to be used as the image name in the container
    """
    try:
        hash = hashlib.sha256(image).hexdigest()
        return hash

    except GenerateHashError as error:
        print(error)


async def mount_container(connection_string, container_uuid, create_container=True):
    """
    given a connection string and a container name, mounts the container and
    returns the container client as an object that can be used in other functions.
    if a specified container doesnt exist, it creates one with the provided uuid,
    if create_container is True
    """
    try:
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )
        if blob_service_client:
            container_name = "user-{}".format(container_uuid)
            container_client = blob_service_client.get_container_client(container_name)
            if container_client.exists():
                return container_client
            elif create_container and not container_client.exists():
                container_client = blob_service_client.create_container(container_name)
                # create general directory for new user container
                response = await create_folder(container_client, "General")
                if response:
                    return container_client
                else:
                    return False
        else:
            raise ConnectionStringError("Invalid connection string")

    except MountContainerError as error:
        print(error)
        return False


async def get_blob(container_client, blob_name):
    """
    gets the contents of a specified blob in the user's container
    """
    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob = blob_client.download_blob()
        blob_content = blob.readall()
        return blob_content

    except GetBlobError as error:
        print(error)
        return False


async def upload_image(container_client, folder_name, image, hash_value):
    """
    uploads the image to the specified folder within the user's container,
    if the specified folder doesnt exist, it creates it with a uuid
    """
    try:
        directories = await get_directories(container_client)
        if folder_name not in directories:
            folder_uuid = uuid.uuid4()
            folder_data = {
                "folder_name": folder_name,
                "date_created": str(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
            }
            image_name = "{}/{}.png".format(folder_uuid, hash_value)
            folder_name = "{}/{}.json".format(folder_uuid, folder_uuid)
            container_client.upload_blob(image_name, image, overwrite=True)
            container_client.upload_blob(
                folder_name, json.dumps(folder_data), overwrite=True
            )
            return image_name
        else:
            folder_uuid = await get_folder_uuid(container_client, folder_name)
            blob_name = "{}/{}.png".format(folder_uuid, hash_value)
            container_client.upload_blob(blob_name, image, overwrite=True)
            return blob_name

    except UploadImageError as error:
        print(error)
        return False


async def create_folder(container_client, folder_name):
    """
    creates a folder in the user's container
    """
    try:
        directories = await get_directories(container_client)
        if folder_name not in directories:
            folder_uuid = uuid.uuid4()
            folder_data = {
                "folder_name": folder_name,
                "date_created": str(
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
            }
            folder_name = "{}/{}.json".format(folder_uuid, folder_uuid)
            container_client.upload_blob(
                folder_name, json.dumps(folder_data), overwrite=True
            )
            return True
        else:
            return False

    except CreateDirectoryError as error:
        print(error)
        return False


async def upload_inference_result(container_client, folder_name, result, hash_value):
    """
    uploads the inference results json file to the specified folder
    in the users container
    """
    try:
        folder_uuid = await get_folder_uuid(container_client, folder_name)
        if folder_uuid:
            json_name = "{}/{}.json".format(folder_uuid, hash_value)
            container_client.upload_blob(json_name, result, overwrite=True)
            return True

    except UploadInferenceResultError as error:
        print(error)
        return False


async def get_folder_uuid(container_client, folder_name):
    """
    gets the uuid of a folder in the user's container given the folder name by
    iterating through the folder json files and extracting the name
    to match given folder name
    """
    try:
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            if (
                blob.name.split(".")[-1] == "json"
                and blob.name.count("/") == 1
                and blob.name.split("/")[0] == blob.name.split("/")[1].split(".")[0]
            ):
                folder_json = await get_blob(container_client, blob.name)
                if folder_json:
                    folder_json = json.loads(folder_json)
                    if folder_json["folder_name"] == folder_name:
                        return blob.name.split(".")[0].split("/")[-1]
        return False
    except GetFolderUUIDError as error:
        print(error)
        return False


async def get_image_count(container_client, folder_name):
    """
    gets the number of images in a folder in the user's container
    """
    try:
        folder_uuid = await get_folder_uuid(container_client, folder_name)
        if folder_uuid:
            blob_list = container_client.list_blobs()
            count = 0
            for blob in blob_list:
                if (blob.name.split("/")[0] == folder_uuid) and (
                    blob.name.split(".")[-1] == "png"
                ):
                    count += 1
            return count
        else:
            return False
    except GetFolderUUIDError as error:
        print(error)
        return False


async def get_directories(container_client):
    """
    returns a list of folder names in the user's container
    """
    try:
        directories = {}
        blob_list = container_client.list_blobs()
        for blob in blob_list:
            if (
                blob.name.split(".")[-1] == "json"
                and blob.name.count("/") == 1
                and blob.name.split("/")[0] == blob.name.split("/")[1].split(".")[0]
            ):
                json_blob = await get_blob(container_client, blob.name)
                if json_blob:
                    folder_json = json.loads(json_blob)
                    image_count = await get_image_count(
                        container_client, folder_json["folder_name"]
                    )
                    directories[folder_json["folder_name"]] = image_count
        return directories
    except FolderListError as error:
        print(error)
        return []
