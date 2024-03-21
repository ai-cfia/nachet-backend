import random
import numpy as np
from custom_exceptions import ProcessInferenceResultError

async def process_inference_results(data: dict, imageDims: list[int, int], area_ratio: float = 0.5) -> dict:
    """
    Process the inference results by performing various operations on the data.
      Indicate if there are overlapping boxes and calculate the label
      occurrence. The overlapping is determined if the common area of two boxes
      is greater than the area_ratio (default = 0.5) of the area of each box.

    Args:
        data (dict): The inference results data.
        imageDims (tuple): The dimensions of the image.
        area_ratio (float): The area ratio of a box to consider the overlapping

    Returns:
        dict: The processed inference results data.

    Raises:
        ProcessInferenceResultError: If there is an error processing the
        inference results.
    """
    try:
        boxes = data[0]['boxes']
        colors = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in boxes]
        # Perform operations on each box in the data
        for i, box in enumerate(boxes):
            # Set default overlapping attribute to false for each box
            boxes[i]["overlapping"] = False
            # Set default overlapping indices to empty array for each box
            boxes[i]["overlappingIndices"] = []

            # Perform calculations on box coordinates
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

        # Check if there are any overlapping boxes, if so, put the lower score
        # box in the overlapping key
        for i, box in enumerate(boxes):
            for j, box2 in enumerate(boxes):
                if j > i:
                    # Calculate the common region of the two boxes to determine
                    # if they are overlapping
                    area_box = (box["box"]["bottomX"] - box["box"]["topX"]) * (box["box"]["bottomY"] - box["box"]["topY"])
                    area_candidate = (box2["box"]["bottomX"] - box2["box"]["topX"]) * (box2["box"]["bottomY"] - box2["box"]["topY"])

                    intersection_topX = max(box["box"]["topX"], box2["box"]["topX"])
                    intersection_topY = max(box["box"]["topY"], box2["box"]["topY"])
                    intersection_bottomX = min(box["box"]["bottomX"], box2["box"]["bottomX"])
                    intersection_bottomY = min(box["box"]["bottomY"], box2["box"]["bottomY"])

                    width = max(0, intersection_bottomX - intersection_topX)
                    height = max(0, intersection_bottomY - intersection_topY)

                    common_area = width * height

                    if common_area >= area_box * area_ratio and common_area >= area_candidate * area_ratio:
                        # box2 is the lower score box
                        if box2["score"] < box["score"]:
                            boxes[j]["overlapping"] = True
                            boxes[i]["overlappingIndices"].append(j + 1)
                            box2["box"]["bottomX"] = box["box"]["bottomX"]
                            box2["box"]["bottomY"] = box["box"]["bottomY"]
                            box2["box"]["topX"] = box["box"]["topX"]
                            box2["box"]["topY"] = box["box"]["topY"]
                        # box is the lower score box
                        elif box["score"] < box2["score"]:
                            boxes[i]["overlapping"] = True
                            boxes[i]["overlappingIndices"].append(j + 1)
                            box["box"]["bottomX"] = box2["box"]["bottomX"]
                            box["box"]["bottomY"] = box2["box"]["bottomY"]
                            box["box"]["topX"] = box2["box"]["topX"]
                            box["box"]["topY"] = box2["box"]["topY"]

        # Calculate label occurrence
        labelOccurrence = {}
        label_colors = {}
        for i, box in enumerate(data[0]["boxes"]):
            if box["label"] not in labelOccurrence:
                labelOccurrence[box["label"]] = 1
                label_colors[box["label"]] = colors[i]
                box["color"] = colors[i]

            else:
                labelOccurrence[box["label"]] += 1
                box["color"] = label_colors[box["label"]]
        data[0]["labelOccurrence"] = labelOccurrence

        # Add totalBoxes attribute to the inference results
        data[0]["totalBoxes"] = sum(1 for _ in data[0]["boxes"])

        return data

    except (KeyError, TypeError, IndexError) as error:
        print(error)
        raise ProcessInferenceResultError("Error processing inference results") from error
