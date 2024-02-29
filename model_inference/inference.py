import numpy as np
import io
import base64
from PIL import Image
from custom_exceptions import ProcessInferenceResultError

async def process_image_slicing(image_bytes: bytes, result_json: dict) -> list:
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

async def process_swin_result(img_box:dict, results: dict) -> list:
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
    
    return img_box

async def process_inference_results(data, imageDims):
    """
    processes the pipeline (last output) inference results to add additional attributes
    to the inference results that are used in the frontend
    """
    try:
        data = data
        for i, box in enumerate(data[0]["boxes"]):
            # set default overlapping attribute to false for each box
            data[0]["boxes"][i]["overlapping"] = False
            # set default overlappingindices to empty array for each box
            data[0]["boxes"][i]["overlappingIndices"] = []
            box["box"]["bottomX"] = int(
                np.clip(box["box"]["bottomX"] * imageDims[0], 5, imageDims[0] - 5)
            )
            box["box"]["bottomY"] = int(
                np.clip(box["box"]["bottomY"] * imageDims[1], 5, imageDims[1] - 5)
            )
            box["box"]["topX"] = int(
                np.clip(box["box"]["topX"] * imageDims[0], 5, imageDims[0] - 5)
            )
            box["box"]["topY"] = int(
                np.clip(box["box"]["topY"] * imageDims[1], 5, imageDims[1] - 5)
            )
        # check if there any overlapping boxes, if so, put the lower score box
        # in the overlapping key
        for i, box in enumerate(data[0]["boxes"]):
            for j, box2 in enumerate(data[0]["boxes"]):
                if j > i:
                    if (
                        box["box"]["bottomX"] >= box2["box"]["topX"]
                        and box["box"]["bottomY"] >= box2["box"]["topY"]
                        and box["box"]["topX"] <= box2["box"]["bottomX"]
                        and box["box"]["topY"] <= box2["box"]["bottomY"]
                    ):
                        if box["score"] >= box2["score"]:
                            data[0]["boxes"][j]["overlapping"] = True
                            data[0]["boxes"][i]["overlappingIndices"].append(j + 1)
                            box2["box"]["bottomX"] = box["box"]["bottomX"]
                            box2["box"]["bottomY"] = box["box"]["bottomY"]
                            box2["box"]["topX"] = box["box"]["topX"]
                            box2["box"]["topY"] = box["box"]["topY"]
                        else:
                            data[0]["boxes"][i]["overlapping"] = True
                            data[0]["boxes"][i]["overlappingIndices"].append(j + 1)
                            box["box"]["bottomX"] = box2["box"]["bottomX"]
                            box["box"]["bottomY"] = box2["box"]["bottomY"]
                            box["box"]["topX"] = box2["box"]["topX"]
                            box["box"]["topY"] = box2["box"]["topY"]
        labelOccurrence = {}
        for i, box in enumerate(data[0]["boxes"]):
            if box["label"] not in labelOccurrence:
                labelOccurrence[box["label"]] = 1
            else:
                labelOccurrence[box["label"]] += 1
        data[0]["labelOccurrence"] = labelOccurrence
        # add totalBoxes attribute to the inference results
        data[0]["totalBoxes"] = sum(1 for box in data[0]["boxes"])
        return data

    except ProcessInferenceResultError as error:
        print(error)
        return False
