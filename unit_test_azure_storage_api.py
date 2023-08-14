import unittest
from unittest.mock import patch
import asyncio
from azure_storage_api import *
from mock_objects import *


class TestMountContainer(unittest.TestCase):

    def test_container_exists(self):
        
        # arrange mock objects
        mock_blob_service_client = BlobServiceClientMock("connection_string_1")
        mock_client_container = ContainerClientMock("container_client_1")

        # act

        # assert

    def test_invalid_container(self):
        pass








if __name__ == '__main__':
    unittest.main()
