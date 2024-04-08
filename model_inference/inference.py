"""
This module provides functions to process the inference results from a given
pipelines.

It returns the processed inference results with additional information such as
overlapping boxes, label occurrence, and colors for each species found.

The colors can be returned in HEX or RGB format depending on the frontend preference.
The colors are based on the colormaps from matplotlib.
"""

import numpy as np

from custom_exceptions import ProcessInferenceResultError

from model_inference.color_palette import get_color_palettes


async def process_inference_results(
        data: dict,
        imageDims: list[int, int],
        area_ratio: float = 0.5,
        color_format: str = "hex"
) -> dict:
    """
    Process the inference results by performing various operations on the data.
      Indicate if there are overlapping boxes and calculates the label
      occurrence. Boxes can overlap if their common area is greater than the
      area_ratio (default = 0.5) of the area of each box.

    Args:
        data (dict): The inference result data.
        imageDims (tuple): The dimensions of the image.
        area_ratio (float): The area ratio of a box to consider in the box
        overlap claculation.
        color_set (str): The color set to use.
        color_format (str): Specified the format representation of the color.
        Support hex and rgb.

    Returns:
        dict: The processed inference result data.

    Raises:
        ProcessInferenceResultError: If there is an error processing the
        inference results.
    """
    try:
        boxes = data[0]['boxes']

        if color_format == "hex":
            colors = get_color_palettes()
            over_colors = get_color_palettes(set_="set2")
        elif color_format == "rgb":
            colors = get_color_palettes(format_=color_format)
            over_colors = get_color_palettes(set_="set2", format_=color_format)

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
                    area_box = (box["box"]["bottomX"] - box["box"]["topX"]) \
                                * (box["box"]["bottomY"] - box["box"]["topY"])
                    area_candidate = (box2["box"]["bottomX"] - box2["box"]["topX"]) \
                                    * (box2["box"]["bottomY"] - box2["box"]["topY"])

                    intersection_topX = max(
                        box["box"]["topX"], box2["box"]["topX"])
                    intersection_topY = max(
                        box["box"]["topY"], box2["box"]["topY"])
                    intersection_bottomX = min(
                        box["box"]["bottomX"], box2["box"]["bottomX"])
                    intersection_bottomY = min(
                        box["box"]["bottomY"], box2["box"]["bottomY"])

                    width = max(0, intersection_bottomX - intersection_topX)
                    height = max(0, intersection_bottomY - intersection_topY)

                    common_area = width * height

                    if common_area >= area_box * area_ratio \
                        and common_area >= area_candidate * area_ratio:
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
        label_occurrence = {}
        label_colors = {}
        for i, box in enumerate(boxes):
            if box["label"] not in label_occurrence:
                label_occurrence[box["label"]] = 1
                if i < len(colors):
                    label_colors[box["label"]] = colors[i]
                    box["color"] = colors[i]
                else:
                    diff = len(over_colors) + 1
                    label_colors[box["label"]] = over_colors[i - diff]
                    box["color"] = over_colors[i - diff]
            else:
                label_occurrence[box["label"]] += 1
                color = label_colors[box["label"]]
                box["color"] = color

        data[0]["labelOccurrence"] = label_occurrence
        data[0]["totalBoxes"] = sum(1 for _ in data[0]["boxes"])

        return data

    except (KeyError, TypeError, IndexError) as error:
        print(error)
        raise ProcessInferenceResultError("Error processing inference results") from error
