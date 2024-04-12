import unittest
import asyncio

from app import app, json, base64, Image, io
from unittest.mock import patch, Mock


class TestImageBatchImport(unittest.TestCase):
    def setUp(self):
        self.test_client = app.test_client()

    def tearDown(self):
        pass

    @patch("datastore.db.queries.seed.get_all_seeds_names")
    def test_picture_form_success(self, mock_seed_name):

        expected_result = ["seed_name"]

        mock_seed_name.return_value = ["seed_name"]

        response = asyncio.run(self.test_client.get("/picture-form"))
        result = json.loads(asyncio.run(response.get_data()))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, expected_result)

    @patch("datastore.db.queries.seed.get_all_seeds_names")
    def test_picture_form_failure(self, mock_seed_name):

        expected_result = "Error: seeds could not be retrieved"

        # TODO change with datastore.db.queries.seed.SeedNotFoundError()
        mock_seed_name.side_effect = Exception("Error: seeds could not be retrieved")

        response = asyncio.run(self.test_client.get("/picture-form"))
        result = json.loads(asyncio.run(response.get_data()))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(result, expected_result)

    @patch("datastore.bin.upload_picture_set.upload_picture_set")
    def test_upload_picture_success(self, mock_upload_picture_set):

        expected_result = 1
        mock_upload_picture_set.return_value = 1

        response = asyncio.run(self.test_client.post("/upload-pictures"))
        result = json.loads(asyncio.run(response.get_data()))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(result, expected_result)

    @patch("datastore.bin.upload_picture_set.upload_picture_set")
    def test_upload_picture_failure(self, mock_upload_picture_set):

        expected_result = "An error occured during the upload of the picture set"
        # TODO change with datastore.bin.upload_picture_set.UploadError()
        mock_upload_picture_set.side_effect = Exception("An error occured during the upload of the picture set")

        response = asyncio.run(self.test_client.post("/upload-pictures"))
        result = json.loads(asyncio.run(response.get_data()))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(result, expected_result)
