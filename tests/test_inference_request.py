import unittest
import json
import os
import base64
import asyncio

from app import app
from unittest.mock import patch, MagicMock, Mock

class TestInferenceRequest(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment before running each test case.
        """
        # Start the test pipeline
        self.test = app.test_client()
        response = asyncio.run(
            self.test.get("/test")
        )
        self.pipeline = json.loads(asyncio.run(response.get_data()))[0]
        current_dir = os.path.dirname(__file__)
        image_path = os.path.join(current_dir, '1310_1.png')
        self.endpoints = "/model-endpoints-metadata"
        self.inference = "/inf"
        self.container_name = "bab1da84-5937-4016-965e-67e1ea6e29c4"
        self.folder_name = "test_folder"
        self.image_header = "data:image/PNG;base64,"
        with open(image_path, 'rb') as image_file:
            self.image_src = base64.b64encode(image_file.read()).decode('utf-8')

    def tearDown(self) -> None:
        """
        Tear down the test environment at the end of each test case.
        """
        self.image_src = None
        self.test = None

    @patch("azure_storage.azure_storage_api.mount_container")
    def test_inference_request_successful(self, mock_container):
        # Mock azure client services
        mock_blob = Mock()
        mock_blob.readall.return_value = bytes(self.image_src, encoding="utf-8")

        mock_blob_client = Mock()
        mock_blob_client.configure_mock(name="test_blob.json")
        mock_blob_client.download_blob.return_value = mock_blob

        mock_container_client = MagicMock()
        mock_container_client.list_blobs.return_value = [mock_blob_client]
        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_container_client.exists.return_value = True

        mock_container.return_value = mock_container_client
        # Build expected response keys
        responses = set()
        expected_keys = {
            "filename",
            "boxes",
            "labelOccurrence",
            "totalBoxes",
            "box",
            "label",
            "color",
            "score",
            "topN",
            "overlapping",
            "overlappingIndices"
        }

        # Test the answers from inference_request
        response = asyncio.run(
            self.test.post(
                '/inf',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "image": self.image_header + self.image_src,
                    "imageDims": [720,540],
                    "folder_name": self.folder_name,
                    "container_name": self.container_name,
                    "model_name": self.pipeline.get("pipeline_name")
                })
        )

        result_json = json.loads(asyncio.run(response.get_data()))[0]
        keys = set(result_json.keys())
        keys.update(result_json["boxes"][0].keys())
        responses.update(keys)

        print(expected_keys == responses)
        self.assertEqual(responses, expected_keys)

    @patch("azure_storage.azure_storage_api.mount_container")
    def test_inference_request_unsuccessfull(self, mock_container):
        # Mock azure client services
        mock_blob = Mock()
        mock_blob.readall.return_value = b""

        mock_blob_client = Mock()
        mock_blob_client.configure_mock(name="test_blob.json")
        mock_blob_client.download_blob.return_value = mock_blob

        mock_container_client = MagicMock()
        mock_container_client.list_blobs.return_value = [mock_blob_client]
        mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_container_client.exists.return_value = True

        mock_container.return_value = mock_container_client

        # Build expected response
        expected = 400

        # Test the answers from inference_request
        response = asyncio.run(
            self.test.post(
                '/inf',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "image": self.image_header,
                    "imageDims": [720,540],
                    "folder_name": self.folder_name,
                    "container_name": self.container_name,
                    "model_name": self.pipeline.get("pipeline_name")
                })
        )

        print(expected == response.status_code)
        self.assertEqual(response.status_code, expected)

    def test_inference_request_missing_argument(self):
        # Build expected response
        responses = []
        expected = ("InferenceRequestError: missing request arguments: either folder_name, container_name, imageDims or image is missing")

        data = {
            "image": self.image_header,
            "imageDims": [720,540],
            "folder_name": self.folder_name,
            "container_name": self.container_name,
            "model_name": self.pipeline.get("pipeline_name")
        }

        # Test the answers from inference_request

        for k, v in data.items():
            if k != "model_name":
                data[k] = ""
                response = asyncio.run(
                    self.test.post(
                        '/inf',
                        headers={
                            "Content-Type": "application/json",
                            "Access-Control-Allow-Origin": "*",
                        },
                        json=data
                    )
                )
                result_json = json.loads(asyncio.run(response.get_data()))
                if len(responses) == 0:
                    responses.append(result_json[0])
                if responses[0] != result_json[0]:
                    responses.append(result_json[0])
                data[k] = v

        if len(responses) > 1:
            raise ValueError(f"Different errors messages were given; expected only 'missing request arguments', {responses}")
        print(expected == result_json[0])
        print(response.status_code == 400)
        self.assertEqual(result_json[0], expected)
        self.assertEqual(response.status_code, 400)

    def test_inference_request_wrong_pipeline_name(self):
        # Build expected response
        expected = ("InferenceRequestError: model wrong_pipeline_name not found")

        # Test the answers from inference_request
        response = asyncio.run(
            self.test.post(
                '/inf',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "image": self.image_src,
                    "imageDims": [720,540],
                    "folder_name": self.folder_name,
                    "container_name": self.container_name,
                    "model_name": "wrong_pipeline_name"
                }
            )
        )
        result_json = json.loads(asyncio.run(response.get_data()))

        print(expected == result_json[0])
        print(response.status_code == 400)

        self.assertEqual(result_json[0], expected)
        self.assertEqual(response.status_code, 400)

    def test_inference_request_wrong_header(self):
        # Build expected response
        expected = ("InferenceRequestError: invalid image header")

        # Test the answers from inference_request
        response = asyncio.run(
            self.test.post(
                '/inf',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "image": "data:python," + self.image_src,
                    "imageDims": [720,540],
                    "folder_name": self.folder_name,
                    "container_name": self.container_name,
                    "model_name": self.pipeline.get("pipeline_name")
                }
            )
        )
        result_json = json.loads(asyncio.run(response.get_data()))

        print(expected == result_json[0])
        print(response.status_code == 400)

        self.assertEqual(result_json[0], expected)
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
