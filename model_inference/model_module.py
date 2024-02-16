import urllib.request
import model_request.model_request as reqt
import json

from dataclasses import dataclass
from model_inference.inference import (
    image_slicing,
    swin_result_parser,
)

from custom_exceptions import InferenceRequestError


@dataclass(frozen=True)
class ModelConfig:
    category: int
    name: str
    version: str
    endpoint: str
    api_key: str
    pipeline: list
    return_value: str
    inference_function: list
    
'''
In order to offer a encapsulated and reusable code, model were divided into three types:

Category 1: A model that returns a single result, such as a classification model.
Category 2: A model that returns multiple results, such as an object detection model.
Category 3: A model that returns a single result, but execute the task of a type 2 and type 1 to process get to the result.

The goals of this division are:
To allows the code to be more modular and reusable, since the inference function can be used in different models.
To allows the code to be more scalable, since it is possible to add new types of models without changing the code.
To allows the code to be more maintainable, since the code is more organized and easier to understand.
'''


async def type_one_model_inference(model: tuple, previous_result):
    """
    Perform inference using a type one model.

    Args:
        model (tuple): A tuple containing the model configuration.
        previous_result: The previous result to be used for inference.

    Returns:
        dict or tuple: If the test result is not "seed", returns the result JSON.
                      If the test result is "seed", returns a dictionary containing the result JSON
                      and the sliced image.
    """
    try:
        model_config = ModelConfig(*model)

        result_json = []
        for img in previous_result.get("image_sliced"):
            req = await reqt.request_factory(img, model_config.endpoint, model_config.api_key, model_config.name)
            response = urllib.request.urlopen(req)
            result = response.read()
            result_json.append(json.loads(result.decode("utf8")))

        return await swin_result_parser(previous_result.get("result_json"), result_json)
    except Exception as e:
       raise InferenceRequestError(f"An error occurred while processing the request:\n {str(e)}")


async def type_two_model_inference(model: tuple, previous_result):
    """
    Perform model inference using a type two model.

    Args:
        model (tuple): A tuple containing the model configuration parameters.
        previous_result: The previous result obtained from the model inference.

    Returns:
        The parsed result obtained from the model inference.
    """
    try:
        model_config = ModelConfig(*model)

        req = await reqt.request_factory(previous_result, model_config.endpoint, model_config.api_key, model_config.name)
        response = urllib.request.urlopen(req)
        result = response.read()
        result_json = json.loads(result.decode("utf8"))

        return {
            "result_json": result_json,
            "image_sliced": await image_slicing(previous_result, result_json)
        }
    except Exception as e:
        raise InferenceRequestError(f"An error occurred while processing the request:\n {str(e)}")
    

async def type_three_model_inference(model: tuple, previous_result):
    """
    Perform model inference using a type three model.

    Args:
        model (tuple): A tuple containing the model configuration parameters.
        previous_result: The previous result obtained from the model inference.

    Returns:
        The parsed result obtained from the model inference.
    """
    try:
        model_config = ModelConfig(*model)

        req = await reqt.request_factory(previous_result, model_config.endpoint, model_config.api_key, model_config.name)
        response = urllib.request.urlopen(req)
        result = response.read()
        return json.loads(result.decode("utf8"))
    
    except Exception as e:
       raise InferenceRequestError(f"An error occurred while processing the request:\n {str(e)}")
