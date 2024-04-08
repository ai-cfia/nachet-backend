import io
import base64
import json
from PIL import Image
from urllib.request import Request

async def image_slicing(image_bytes: bytes, result_json: dict) -> list:
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
    for i, result in enumerate(results):
        img_box[0]['boxes'][i]['label'] = [d.get("label") for d in result]
        img_box[0]['boxes'][i]['score'] = [d.get("score") for d in result]

    return img_box

async def seed_detector_header(api_key: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": ("Bearer " + api_key),
        "azureml-model-deployment": "seed-detector-1",
    }

async def swin_header(api_key: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": ("Bearer " + api_key),
    }

# Eventually the goals would be to have a request factory that would return
# a request for the specified models such as the following:
async def request_factory(img_bytes: str | bytes, endpoint_url: str, api_key: str, model_name: str) -> Request:
    """
    Return a request for calling AzureML AI model
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
