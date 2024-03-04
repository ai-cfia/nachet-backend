import json
from collections import namedtuple
from urllib.request import Request

async def request_factory(img_bytes: str | bytes, model: namedtuple) -> Request:
    """
    Args:
        img_bytes (str | bytes): The image data as either a string or bytes.
         model: (namedtuple): A tuple containing all the information necessary
         to get the model inference.
    Returns:
        Request: The request object for calling the AI model.
    """

    supported_deployment_platform = {"azure", "google", "huggingface", "aws"}
    deployment_platform = list(model.deployment_platform.keys())[0]

    headers = {
        "Content-Type": model.content_type, #"application/json"
        "Authorization": ("Bearer " + model.api_key),
        # "azureml-model-deployment": model.name,
    }

    if deployment_platform in supported_deployment_platform:
        headers[model.deployment_platform[deployment_platform]] = model.name

    if isinstance(img_bytes, str):
        data = {
            "input_data": {
                "columns": ["image"],
                "index": [0],
                "data": [img_bytes],
            }
        }
        body = str.encode(json.dumps(data))
    elif isinstance(img_bytes, bytes):
        body = img_bytes

    return Request(model.endpoint, body, headers)
