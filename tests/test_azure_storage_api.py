import unittest
from unittest.mock import patch, Mock
import uuid
import json
import datetime
from azure_storage.azure_storage_api import (
    mount_container,
    get_blob,
    upload_image,
)
from custom_exceptions import (
    ConnectionStringError,
    MountContainerError,
    GetBlobError,
    UploadImageError,
    UploadInferenceResultError,
    GetFolderUUIDError,
    FolderListError,
    GenerateHashError,
)

import asyncio


class TestMountContainerFunction(unittest.TestCase):
    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_mount_existing_container(self, MockFromConnectionString):
        # mock the client container
        mock_container_client = Mock()
        mock_container_client.exists.return_value = True
        # mock the blob service client
        mock_blob_service_client = MockFromConnectionString.return_value
        mock_blob_service_client.get_container_client.return_value = (
            mock_container_client
        )

        connection_string = "test_connection_string"
        container_name = "testcontainer"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            mount_container(connection_string, container_name)
        )

        print(result == mock_container_client)

        self.assertEqual(result, mock_container_client)

    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_mount_nonexisting_container_create(self, MockFromConnectionString):
        """
        tests when a container does not exists and create_container flag is set to True,
        should create a new container and return the container client
        """
        # mock the client container and blob service client
        mock_container_client = Mock()
        mock_container_client.exists.return_value = False

        mock_blob_service_client = MockFromConnectionString.return_value
        mock_blob_service_client.get_container_client.return_value = (
            mock_container_client
        )

        # Simulate that a new container is created
        mock_new_container_client = Mock()
        mock_blob_service_client.create_container.return_value = (
            mock_new_container_client
        )

        connection_string = "test_connection_string"
        container_name = "testcontainer"
        expected_container_name = "user-{}".format(container_name)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            mount_container(
                connection_string, container_name, create_container=True
            )
        )

        mock_blob_service_client.create_container.assert_called_once_with(
            expected_container_name
        )
        print(result == mock_new_container_client)
        self.assertEqual(result, mock_new_container_client)

    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_mount_nonexisting_container_no_create(self, MockFromConnectionString):
        mock_container_client = Mock()
        mock_container_client.exists.return_value = False

        mock_blob_service_client = MockFromConnectionString.return_value
        mock_blob_service_client.get_container_client.return_value = (
            mock_container_client
        )

        connection_string = "test_connection_string"
        container_name = "testcontainer"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            mount_container(
                connection_string, container_name, create_container=False
            )
        )

        mock_blob_service_client.create_container.assert_not_called()
        print(result == None)
        self.assertEqual(result, None)


class TestGetBlob(unittest.TestCase):
    
    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_get_blob_successful(self, MockFromConnectionString):
        mock_blob_name = "test_blob"
        mock_blob_content = b"blob content"
        
        mock_blob = Mock()
        mock_blob.readall.return_value = mock_blob_content
        
        mock_blob_client = Mock()
        mock_blob_client.download_blob.return_value = mock_blob
        
        mock_container_client = Mock()
        mock_container_client.get_blob_client.return_value = mock_blob_client

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            get_blob(mock_container_client, mock_blob_name)
        )

        print(result == mock_blob_content)
        
        self.assertEqual(result, mock_blob_content)

    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_get_blob_unsuccessful(self, MockFromConnectionString):
        mock_blob_name = "test_blob"
        mock_blob_content = b"blob content"
        
        mock_blob = Mock()
        mock_blob.readall.return_value = mock_blob_content
        
        mock_blob_client = Mock()
        mock_blob_client.download_blob.side_effect = GetBlobError("Blob not found")
        
        mock_container_client = Mock()
        mock_container_client.get_blob_client.return_value = mock_blob_client

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            get_blob(mock_container_client, "nonexisting_blob")
        )

        print(result == False)

        self.assertEqual(result, False)

if __name__ == "__main__":
    unittest.main()
