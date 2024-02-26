"""
This module contains functions for performing inference using different models.

Functions:
    request_inference_from_swin: Perform inference using the SWIN model on a list of images.
    request_inference_from_seed_detector: Requests inference from the seed detector model using the provided previous result.
    request_inference_from_nachet_six_seed: Requests inference from the Nachet Six Seed model.
"""
import urllib.request
import model_request.model_request as reqt
import json
from collections import namedtuple
from custom_exceptions import InferenceRequestError



async def request_inference_from_swin(model: namedtuple, previous_result: list[bytes]):
    """
    Perform inference using the SWIN model on a list of images.

    Args:
        model (namedtuple): The SWIN model to use for inference.
        previous_result (list[bytes]): The previous result containing the images to perform inference on.

    Returns:
        The result of the inference.

    Raises:
        InferenceRequestError: If an error occurs while processing the request.
    """
    try:
        result_json = []
        for img in previous_result.get("images"):
            req = await reqt.request_factory(img, model)
            response = urllib.request.urlopen(req)
            result = response.read()
            result_json.append(json.loads(result.decode("utf8")))

        return await model.inference_function(previous_result.get("result_json"), result_json)
    except Exception as e:
       raise InferenceRequestError(f"An error occurred while processing the request:\n {str(e)}")


async def request_inference_from_seed_detector(model: namedtuple, previous_result: str):
    """
    Requests inference from the seed detector model using the provided previous result.

    Args:
        model (namedtuple): The seed detector model.
        previous_result (str): The previous result used for inference.

    Returns:
        dict: A dictionary containing the result JSON and the images generated from the inference.
    
    Raises:
        InferenceRequestError: If an error occurs while processing the request.
    """
    try:
        req = await reqt.request_factory(previous_result, model)
        response = urllib.request.urlopen(req)
        result = response.read()
        result_json = json.loads(result.decode("utf8"))

        return {
            "result_json": result_json,
            "images": await model.inference_function(previous_result, result_json)
        }
    except Exception as e:
        raise InferenceRequestError(f"An error occurred while processing the request:\n {str(e)}")
    

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
        req = await reqt.request_factory(previous_result, model)
        response = urllib.request.urlopen(req)
        result = response.read()
        result_json = json.loads(result.decode("utf8"))

        return result_json[0],

    except Exception as e:
        raise InferenceRequestError(f"An error occurred while processing the request:\n {str(e)}")
   