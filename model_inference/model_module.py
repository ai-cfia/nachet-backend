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
    task: int
    name: str
    # endpoint_name: str
    version: str
    endpoint: str
    api_key: str
    pipeline: list # TO DO decide if this parameter also contain the position in pipeline
    inference_function: list
    # created_by: str
    # creation_date: str
    # version: str
    # description: str
    # job_name: str
    # dataset: str
    # metrics: list
    # identifiable: list


async def classification_model_inference(model: ModelConfig, previous_result):
    """
    Perform inference using a classification model.

    Args:
        model ModelConfig: Object containing the model configuration parameters.
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


async def object_detection_model_inference(model: ModelConfig, previous_result):
    """
    Perform model inference using a object detection model.

    Args:
        model ModelConfig: Object containing the model configuration parameters.
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
    

async def segmentation_model_inference(model: ModelConfig, previous_result):
    """
    Perform model inference using a segmentation model.

    Args:
        model ModelConfig: Object containing the model configuration parameters.
        previous_result: The previous result obtained from the model inference.

    Returns:
        The parsed result obtained from the model inference.
    """
    pass
    # try:
    #     model_config = ModelConfig(*model)

    #     req = await reqt.request_factory(previous_result, model_config.endpoint, model_config.api_key, model_config.name)
    #     response = urllib.request.urlopen(req)
    #     result = response.read()
    #     return json.loads(result.decode("utf8"))
    
    # except Exception as e:
    #    raise InferenceRequestError(f"An error occurred while processing the request:\n {str(e)}")
