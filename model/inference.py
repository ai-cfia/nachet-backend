
"""
This file contain the generic inference function that process the data at the end
of a given pipeline.
"""

import numpy as np
from custom_exceptions import ProcessInferenceResultError


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
