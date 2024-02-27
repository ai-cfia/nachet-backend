import unittest
from unittest.mock import patch, Mock #, MagicMock
#from custom_exceptions import InferenceRequestError

import json
import asyncio
import os
import base64
import app
from quart.testing import QuartClient

# To test inference_request from app we need to test the following:
# 1 model pipeline
# 2 models pipeline
# pipeline name not matching
# missing one or more blob environment variable
# Return value of the function (JSON) in the following format:

result_json = {
	'filename': 'tmp/tmp_file_name',
	'boxes': [
		{'box': {
				'topX': 0.0,
				'topY': 0.0,
				'bottomX': 0.0,
				'bottomY': 0.0	
			},
		'label': 'label_name',
		'score': 0.999
		}
	],
}

# or

result_json = {
	'filename': 'tmp/tmp_file_name',
	'boxes': [
		{'box': {
				'topX': 0.0,
				'topY': 0.0,
				'bottomX': 0.0,
				'bottomY': 0.0	
			},
		'label': 'label_name',
		'score': 0.999,
        'all_result': [{
                {
                    'label': "seed_name",
                    'score': 0.999
                },
                {
                    'label': "seed_name",
                    'score': 0.002
                },
                {
                    'label': "seed_name",
                    'score': 0.002
                },
                {
                    'label': "seed_name",
                    'score': 0.002
                },
                {
                    'label': "seed_name",
                    'score': 0.002
                }
            }]
		}
	],
}

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
            