import io
import base64
import json
from PIL import Image
from urllib.request import Request

async def image_slicing(image_bytes: bytes, result_json: dict) -> list:
    """
    This function takes the image bytes and the result_json from the model and
    returns a list of cropped images.
    The result_json is expected to be in the following format:
    {
        "boxes": [
            {
                "box": {
                    "topX": 0.0,
                    "topY": 0.0,
                    "bottomX": 0.0,
                    "bottomY": 0.0
                },
                "label": "string",
                "score": 0.0
            }
        ],
    }
    """
    boxes = result_json[0]['boxes']
    image_io_byte = io.BytesIO(base64.b64decode(image_bytes))
    image_io_byte.seek(0)
    image = Image.open(image_io_byte)

    format = image.format

    cropped_images = [bytes(0) for _ in boxes]

    for i, box in enumerate(boxes):
        topX = int(box['box']['topX'] * image.width)
        topY = int(box['box']['topY'] * image.height)
        bottomX = int(box['box']['bottomX'] * image.width)
        bottomY = int(box['box']['bottomY'] * image.height)

        img = image.crop((topX, topY, bottomX, bottomY))

        buffered = io.BytesIO()
        img.save(buffered, format)

        cropped_images[i] = base64.b64encode(buffered.getvalue()) #.decode("utf8")
    
    return cropped_images

async def swin_result_parser(img_box:dict, results: dict) -> list:
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
        img_box[0]['boxes'][i]["all_result"] = [d for d in result]
    
    return img_box

# Eventually the goals would be to have a request factory that would return
# a request for the specified models such as the following:
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
