import unittest
from unittest.mock import patch, Mock
from azure_storage.azure_storage_api import (
    mount_container,
    get_blob,
)
from custom_exceptions import (
    GetBlobError,
)
import app
import asyncio
from quart.testing import QuartClient
import json
import base64
import os

class TestMountContainerFunction(unittest.TestCase):

    def setUp(self):
        # Set up a new event loop for each test
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        # Close the event loop after each test
        self.loop.close()

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


        result = self.loop.run_until_complete(
            mount_container(connection_string, container_name)
        )

        print(result == mock_container_client)

        self.assertEqual(result, mock_container_client)

    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    @patch("azure_storage.azure_storage_api.get_directories")
    def test_mount_nonexisting_container_create(self, mock_get_directories, MockFromConnectionString):
        # Mock the BlobServiceClient
        mock_blob_service_client = MockFromConnectionString.return_value

        # Mock the container client
        mock_container_client = Mock()
        mock_container_client.exists.return_value = False

        # Set the return value for get_container_client
        mock_blob_service_client.get_container_client.return_value = mock_container_client

        # Simulate that a new container is created
        mock_new_container_client = Mock()
        mock_blob_service_client.create_container.return_value = mock_new_container_client

        # Mock get_directories to return an empty dictionary
        mock_get_directories.return_value = {}

        # Test setup
        connection_string = "test_connection_string"
        container_name = "testcontainer"
        expected_container_name = "user-{}".format(container_name)

        # Run the test
        result = self.loop.run_until_complete(
            mount_container(connection_string, container_name, create_container=True)
        )
        self.assertEqual(result, mock_new_container_client)
        mock_blob_service_client.create_container.assert_called_once_with(expected_container_name)


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

        result = self.loop.run_until_complete(
            mount_container(connection_string, container_name, create_container=False)
        )

        mock_blob_service_client.create_container.assert_not_called()
        print(result is None)
        self.assertEqual(result, None)


class TestGetBlob(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

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

        # Use the event loop set up in setUp
        result = self.loop.run_until_complete(
            get_blob(mock_container_client, mock_blob_name)
        )

        self.assertEqual(result, mock_blob_content)

    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_get_blob_unsuccessful(self, MockFromConnectionString):
        mock_blob_content = b"blob content"

        mock_blob = Mock()
        mock_blob.readall.return_value = mock_blob_content

        mock_blob_client = Mock()
        mock_blob_client.download_blob.side_effect = GetBlobError("Blob not found")

        mock_container_client = Mock()
        mock_container_client.get_blob_client.return_value = mock_blob_client

        # Use the event loop set up in setUp
        result = self.loop.run_until_complete(
            get_blob(mock_container_client, "nonexisting_blob")
        )

        self.assertEqual(result, False)

class TestInferenceRequest(unittest.TestCase):
    def setUp(self):
        self.app = app.app
        self.client = QuartClient(self.app)

    def test_valid_inference_request(self):
        asyncio.run(self.async_test_valid_inference_request())

    async def async_test_valid_inference_request(self):
        current_dir = os.path.dirname(__file__)
        image_path = os.path.join(current_dir, '1310_1.png')

        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

        with patch('urllib.request.urlopen') as mock_urlopen:
            # Mock the response from the model endpoint
            mock_response = Mock()
            inference_result = {'result': 'inference_result'}
            mock_response.read.return_value = json.dumps(inference_result).encode()
            mock_urlopen.return_value = mock_response

            # Define a valid request payload with a properly formatted and valid base64 image string
            valid_payload = {
                'folder_name': 'test_folder',
                'container_name': 'test_container',
                'imageDims': [100, 100],
                'image': 'data:image/png;base64,' + encoded_string
            }

            # Send a POST request to the inference endpoint
            response = await self.client.post('/inf', json=valid_payload)
            response_json = await response.get_json()
            self.assertEqual(response.status_code, 200)
            self.assertIn('inference_result', response_json)


if __name__ == "__main__":
    unittest.main()
