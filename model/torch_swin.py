"""
This file contains the function that requests the inference and processes the data from
the swin model.
"""

import json
import base64

from collections import namedtuple
from urllib.error import URLError
from urllib.request import Request, urlopen
from model.model_exceptions import ModelAPIError

class SwinModelAPIError(ModelAPIError) :
    pass

def process_swin_result(img_box:dict, results: dict) -> list:
    """
    Args:
        img_box (dict): The image box containing the bounding boxes and labels.
        results (dict): The results from the model containing the detected seeds.

    Returns:
        list: The updated image box with modified labels and scores.
    """
    for i, result in enumerate(results):
        img_box[0]['boxes'][i]['label'] = result[0].get("label")
        img_box[0]['boxes'][i]['score'] = result[0].get("score")
        img_box[0]['boxes'][i]["topN"] = [d for d in result]
    
    # Adding the "filename" field (mandatory)
    img_box[0]['filename'] = "default_filename"
    
    return img_box


async def request_inference_from_torch_swin(model: namedtuple, previous_result: 'list[bytes]'):
    """
    Perform inference using the SWIN model on a list of images.

    Args:
        model (namedtuple): The SWIN model to use for inference.
        previous_result (list[bytes]): The previous result containing the images to perform inference on.

    Returns:
        The result of the inference.

    Raises:
        ProcessInferenceResultsError: If an error occurs while processing the request.
    """
    try:
        results = []
        for img in previous_result.get("images"):
            headers = {
                "Content-Type": "application/octet-stream",  # Binary content type for image data
                "Authorization": ("Bearer " + model.api_key),
                model.deployment_platform: model.name
            }
            
            # Decode base64 image to binary
            try:
                # Check if the image is already binary or needs decoding
                if isinstance(img, str):
                    # Remove potential base64 prefix like "data:image/jpeg;base64,"
                    if "base64," in img:
                        img = img.split("base64,")[1]
                    image_binary = base64.b64decode(img)
                else:
                    # Assume it's already binary
                    image_binary = img
            except Exception as e:
                raise SwinModelAPIError(f"Failed to decode base64 image: {str(e)}") from e
                
            body = image_binary
            req = Request(model.endpoint, body, headers, method="POST")
            response = urlopen(req)
            result = response.read()
            results.append(json.loads(result.decode("utf8")))

        print(json.dumps(results, indent=4)) #TODO Transform into logging

        return process_swin_result(previous_result.get("result_json"), results)
    except (TypeError, IndexError, AttributeError, URLError, json.JSONDecodeError)  as error:
        print(error)
        raise SwinModelAPIError(f"An error occurred while processing the request:\n {str(error)}") from error
