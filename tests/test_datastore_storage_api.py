import os
import unittest
from app import app
from unittest.mock import patch, MagicMock
import storage.datastore_storage_api as datastore

class TestMissingEnvError(Exception):
    pass

NACHET_DB_URL = os.getenv("NACHET_DB_URL")
NACHET_SCHEMA = os.getenv("NACHET_SCHEMA")

if NACHET_DB_URL is None:
    raise TestMissingEnvError("Missing environment variable: NACHET_AZURE_STORAGE_CONNECTION_STRING")
if NACHET_SCHEMA is None:
    raise TestMissingEnvError("Missing environment variable: NACHET_AZURE_STORAGE_CONNECTION_STRING")

class TestConnection(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment before running each test case.
        """
        self.test_client = app.test_client()
        self.connection = None
    
    def tearDown(self) -> None:
        self.test_client = None
        print(self.connection)
        if self.connection and not self.connection.closed :
            self.connection.close()
        print(self.connection)

    def test_get_connection_successfull(self):
        try :
            self.connection = datastore.get_connection()
            self.assertFalse(self.connection.closed)
        except Exception as e:
            self.fail(f"get_connection() raised an exception: {e}")

    @patch('storage.datastore_storage_api.NACHET_DB_URL', 'postgresql://invalid_url')
    @patch('storage.datastore_storage_api.NACHET_SCHEMA', 'nonexistent_schema')
    def test_get_connection_error_invalid_params(self):
        with self.assertRaises(datastore.DatastoreError):
            self.connection = datastore.get_connection()
    
    def test_get_cursor_successfull(self):
        try :
            self.connection = datastore.get_connection()
            cursor = datastore.get_cursor(self.connection)
            self.assertFalse(cursor.closed)
        except Exception as e:
            self.fail(f"get_cursor() raised an exception: {e}")

    def test_get_cursor_error_invalid_connection(self):
        mock_connection = MagicMock()
        with self.assertRaises(datastore.DatastoreError):
            datastore.get_cursor(mock_connection)


    