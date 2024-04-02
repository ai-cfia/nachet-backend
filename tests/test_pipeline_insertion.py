import unittest

from azure.core.exceptions import ResourceExistsError
from unittest.mock import patch, Mock
from pipelines_version_insertion import (
    insert_new_version_pipeline,
    pipeline_insertion,
    PipelineInsertionError,
    ConnectionStringError,
)

class TestPipelineInsertion(unittest.TestCase):
    """
    Test to perform:
     - Successful pipeline insertion
     - Unsuccessful pipeline insertion
       - File does not exist
       - File extension not supported
       - Not instance of dict
       - Validation Error
         - Missing argument
         - Wrong type
       - Connection String Error
    """

    def setUp(self):
        self.key = Mock()
        self.account_name = "test_storage"
        self.mock_pipeline = {
            "version": "0.0.1",
        }


    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_insert_new_version_pipeline_success(self, mock_connection_string):
        expected_message = "The pipeline was successfully uploaded to the blob storage"

        mock_container_client = Mock()
        mock_container_client.upload_blob.return_value = True

        mock_blob_service_client = mock_connection_string.return_value
        mock_blob_service_client.get_container_client.return_value = (
            mock_container_client
        )

        result = insert_new_version_pipeline(
            self.mock_pipeline, "test_connection_string", self.account_name)

        self.assertEqual(result, expected_message)
        print(result == expected_message)

    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_insert_new_version_pipeline_resouce_exists_error(self, mock_connection_string):

        mock_blob_client = mock_connection_string.return_value
        mock_blob_client.get_container_client.side_effect = ResourceExistsError("Resource not found")

        with self.assertRaises(ConnectionStringError) as context:
            insert_new_version_pipeline(self.mock_pipeline, "test_connection_string", self.account_name)
        print(str(context.exception) == "Resource not found")

    @patch("azure.storage.blob.BlobServiceClient.from_connection_string")
    def test_insert_new_version_pipeline_value_error(self, mock_connection_string):

        mock_connection_string.side_effect = ValueError("Connection string is either blank or malformed.")

        with self.assertRaises(ConnectionStringError) as context:
            insert_new_version_pipeline(self.mock_pipeline, "test_connection_string", self.account_name)
        print(str(context.exception) == "Connection string is either blank or malformed.")

    def test_pipeline_insertion_file_not_exist(self):
        expected = """
            \nthe file does not exist, please check the file path
            \nprovided path: test_file.yaml
            """

        with self.assertRaises(PipelineInsertionError) as context:
            pipeline_insertion("test_file.yaml")
        print(str(context.exception) == expected)

    @patch("os.path.exists")
    def test_pipeline_insertion_file_extension_not_supported(self, mock_os_path_exists):
        expected = """\nthe file must be a json, a yaml or yml file,
            \nplease check the file extension\nprovided extension: md"""

        mock_os_path_exists.return_value = True

        with self.assertRaises(PipelineInsertionError) as context:
            pipeline_insertion("test_file.md")
        print(str(context.exception) == expected)

    @patch("pipelines_version_insertion.yaml_to_json")
    @patch("os.path.exists")
    def test_pipeline_insertion_not_dict(self, mock_os_path_exists, mock_yaml_to_json):
        expected = """\nthe file must contain a dictionary with the following keys:
            \n version, date, pipelines, models \n instead provided a <class 'list'>
            """
        mock_os_path_exists.return_value = True
        mock_yaml_to_json.return_value = []

        with self.assertRaises(PipelineInsertionError) as context:
            pipeline_insertion("test_file.yaml")
        print(str(context.exception) == expected)

    @patch("pipelines_version_insertion.yaml_to_json")
    @patch("os.path.exists")
    def test_pipeline_insertion_fail_validation(self, mock_os_path_exists, mock_yaml_to_json):
        mock_os_path_exists.return_value = True
        mock_yaml_to_json.return_value = {
            "version": "0.0.0",
            "date": "2021-01-01",
            "pipelines": [{"models":1}],
            "models": [],
        }

        # Missing argument and Wrong Type
        with self.assertRaises(PipelineInsertionError):
            pipeline_insertion("test_file.yaml")

    @patch("pipelines_version_insertion.yaml_to_json")
    @patch("os.path.exists")
    def test_pipeline_insertion_fail_no_default(self, mock_os_path_exists, mock_yaml_to_json):
        mock_os_path_exists.return_value = True
        mock_yaml_to_json.return_value = {
            "version": "0.0.0",
            "date": "2021-01-01",
            "pipelines": [
                    {
                        "models": ["test_model"],
                        "model_name": "p_test",
                        "pipeline_name": "p_test",
                        "created_by": "test",
                        "creation_date": "test",
                        "version": 1,
                        "description": "test",
                        "job_name": "test",
                        "dataset": "test",
                        "metrics": [],
                        "identifiable": [],
                        "default": False
                    }
                ],
            "models": [
                {
                    "task": "test",
                    "api_call_function": "test",
                    "endpoint": "test",
                    "api_key": "test",
                    "inference_function": "test",
                    "content_type": "test",
                    "deployment_platform": "test",
                    "endpoint_name": "test",
                    "model_name": "test_model",
                    "created_by": "test",
                    "creation_date": "test",
                    "version": 1,
                    "description": "test",
                    "job_name": "test",
                    "dataset": "test",
                    "metrics": ["test"],
                    "identifiable": ["test"]
                }
            ],
        }

        expected = "no pipeline was set as default, please set one as default by setting the default value as True"
        with self.assertRaises(PipelineInsertionError) as context:
            pipeline_insertion("test_file.yaml")

        self.assertEqual(str(context.exception), expected)
        print(str(context.exception) == expected)

if __name__ == "__main__":
    unittest.main()
