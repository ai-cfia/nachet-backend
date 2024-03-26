"""
This file contains the function that requests the inference and processes the data from
the nachet-6seeds model.
"""

import json
from collections import namedtuple
from urllib.request import Request, urlopen, HTTPError
from custom_exceptions import InferenceRequestError

async def request_inference_from_nachet_6seeds(model: namedtuple, previous_result: str):
    """
    Requests inference from the Nachet Six Seed model.

    Args:
        model (namedtuple): The model to use for inference.
        previous_result (str): The previous result to pass to the model.

    Returns:
        dict: The result of the inference as a JSON object.

    Raises:
        InferenceRequestError: If an error occurs while processing the request.
    """
    try:
        headers = {
            "Content-Type": model.content_type,
            "Authorization": ("Bearer " + model.api_key),
            model.deployment_platform: model.name
        }

        data = {
            "input_data": {
                "columns": ["image"],
                "index": [0],
                "data": [previous_result],
            }
        }
        body = str.encode(json.dumps(data))

        req = Request(model.endpoint, body, headers)
        response = urlopen(req)
        result = response.read()
        result_object = json.loads(result.decode("utf8"))

        print(json.dumps(result_object[0].get("boxes"), indent=4)) # Transform into logging

        return result_object

    except HTTPError as e:
        raise InferenceRequestError(f"An error occurred while processing the request:\n {str(e)}") from None
