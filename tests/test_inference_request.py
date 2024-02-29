import unittest
import requests
import json
import os
import base64

from subprocess import Popen


class TestInferenceRequest(unittest.TestCase):
    def setUp(self) -> None:
        """
        Set up the test environment before running each test case.
        """
        current_dir = os.path.dirname(__file__)
        image_path = os.path.join(current_dir, '1310_1.png')
        self.path = os.path.join(os.getcwd(), 'app.py')
        self.url = "http://localhost:8080/"
        self.endpoints = "model-endpoints-metadata"
        self.inference = "inf"
        self.container_name = "bab1da84-5937-4016-965e-67e1ea6e29c4"
        self.folder_name = "43d43a71-5026-474b-af61-98b98d365db1"
        self.image_header = "data:image/PNG;base64,"
        
        with open(image_path, 'rb') as image_file:
            self.image_src = base64.b64encode(image_file.read()).decode('utf-8')
        self.process = Popen(['python', self.path])

    def tearDown(self) -> None:
        """
        Tear down the test environment at the end of each test case.
        """
        self.process.terminate()
        self.image_src = None

    def test_inference_request_successful(self):
        url = self.url + self.inference
        responses = set()
        expected_keys = {
            "filename",
            "boxes",
            "labelOccurrence",
            "totalBoxes",
            "box",
            "label",
            "score",
            "topN",
            "overlapping",
            "overlappingIndices"
        }

        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }

        data = {
            "image": self.image_header + self.image_src,
            "imageDims": [720,540],
            "folder_name": self.folder_name,
            "container_name": self.container_name
        }

        response = requests.get(self.url+self.endpoints)
        pipelines = json.loads(response.content)

        for pipeline in pipelines:
            data["model_name"] = pipeline.get("pipeline_name")
            response = requests.post(url, headers=headers, json=data)
            result_json = json.loads(response.content)
            keys = set(result_json[0].keys())
            keys.update(result_json[0]["boxes"][0].keys())
            responses.update(keys)

        print(expected_keys == responses)
        self.assertEqual(responses, expected_keys)

    def test_inference_request_unsuccessfull(self):
        url = self.url + self.inference
        expected = 500

        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }

        data = {
            "image": self.image_header,
            "imageDims": [720,540],
            "folder_name": self.folder_name,
            "container_name": self.container_name
        }

        response = requests.get(self.url+self.endpoints)
        pipelines = json.loads(response.content)

        data["model_name"] = pipelines[0].get("pipeline_name")
        response = requests.post(url, headers=headers, json=data)

        print(expected == response.status_code)
        self.assertEqual(response.status_code, expected)

    def test_inference_request_missing_argument(self):
        url = self.url + self.inference
        responses = []
        expected = ("missing request arguments")

        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }

        data = {
            "image": self.image_header + self.image_src,
            "imageDims": [720,540],
            "folder_name": self.folder_name,
            "container_name": self.container_name
        }

        response = requests.get(self.url+self.endpoints)
        pipelines = json.loads(response.content)
        data["model_name"] = pipelines[0].get("pipeline_name")

        for k, v in data.items():
            if k != "model_name":
                data[k] = ""
                response = requests.post(url, headers=headers, json=data)
                result_json = json.loads(response.content)
                if len(responses) == 0:
                    responses.append(result_json[0])
                if responses[0] != result_json[0]:
                    responses.append(result_json[0])
                data[k] = v

        if len(responses) > 1:
            raise ValueError(f"Different errors messages were given; expected only missing request arguments, {responses}")
        
        print(expected == result_json[0])
        self.assertEqual(result_json[0], expected)

    def test_inference_request_wrong_pipeline_name(self):

        url = self.url + self.inference
        expected = ("Model wrong_pipeline_name not found")

        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }

        data = {
            "image": self.image_src,
            "imageDims": [720,540],
            "folder_name": self.folder_name,
            "container_name": self.container_name
        }

        data["model_name"] = "wrong_pipeline_name"
        response = requests.post(url, headers=headers, json=data)
        result_json = json.loads(response.content)

        print(expected == result_json[0])
        self.assertEqual(result_json[0], expected)

    def test_inference_request_wrong_header(self):
         
        url = self.url + self.inference
        expected = ("Invalid image header")
        self.image_header = "data:python/,"

        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }

        data = {
            "image": self.image_header + self.image_src,
            "imageDims": [720,540],
            "folder_name": "43d43a71-5026-474b-af61-98b98d365db1",
            "container_name": "bab1da84-5937-4016-965e-67e1ea6e29c4"
        }

        response = requests.get(self.url+self.endpoints)
        pipelines = json.loads(response.content)

        data["model_name"] = pipelines[0].get("pipeline_name")
        response = requests.post(url, headers=headers, json=data)
        result_json = json.loads(response.content)

        print(expected == result_json[0])
        self.assertEqual(result_json[0], expected)

if __name__ == '__main__':
    unittest.main()
 