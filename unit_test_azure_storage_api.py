import unittest
from unittest.mock import patch, Mock
import azure_storage_api
from custom_exceptions import *
import asyncio


class TestMountContainerFunction(unittest.TestCase):
    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_mount_existing_container(self, MockFromConnectionString):
        mock_container_client = Mock()
        mock_container_client.exists.return_value = True

        mock_blob_service_client = MockFromConnectionString.return_value
        mock_blob_service_client.get_container_client.return_value = (
            mock_container_client
        )

        connection_string = "test_connection_string"
        container_name = "testcontainer"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            azure_storage_api.mount_container(connection_string, container_name)
        )

        print("Result:", result)
        print("Mock Container Client:", mock_container_client)

        self.assertEqual(result, mock_container_client)

    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_mount_nonexisting_container_create(self, MockFromConnectionString):
        """
        tests when a container does not exists and create_container flag is set to True, should create a new container and return the container client
        """
        # Mocking the BlobServiceClient and ContainerClient
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

        # Test
        connection_string = "test_connection_string"
        container_name = "testcontainer"

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            azure_storage_api.mount_container(
                connection_string, container_name, create_container=True
            )
        )

        # Assertions
        mock_blob_service_client.create_container.assert_called_once_with(
            container_name
        )
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
            azure_storage_api.mount_container(
                connection_string, container_name, create_container=False
            )
        )

        mock_blob_service_client.create_container.assert_not_called()
        self.assertEqual(result, None)


if __name__ == "__main__":
    unittest.main()
