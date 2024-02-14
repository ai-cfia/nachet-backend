import json
from urllib.request import Request

async def request_factory(img_bytes: str | bytes, endpoint_url: str, api_key: str, model_name: str) -> Request:
    """
    Args:
        img_bytes (str | bytes): The image data as either a string or bytes.
        endpoint_url (str): The URL of the AI model endpoint.
        api_key (str): The API key for accessing the AI model.

    Returns:
        Request: The request object for calling the AI model.
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": ("Bearer " + api_key),
        "azureml-model-deployment": model_name,
    }

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

    return Request(endpoint_url, body, headers)
