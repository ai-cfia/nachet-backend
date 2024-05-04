"""
This module contains functions for testing the inference procedure in
the backend.
"""
from collections import namedtuple

from model.inference import ProcessInferenceResultError


async def request_inference_from_test(model: namedtuple, previous_result: str):
    """
    Requests a test case inference.

    Args:
        model (namedtuple): The model to use for the test inference.
        previous_result (str): The previous result to pass to the model.

    Returns:
        dict: The result of the inference as a JSON object.

    Raises:
        InferenceRequestError: If an error occurs while processing the request.
    """
    try:
        if previous_result == '':
           raise ValueError("The result send to the inference function is empty")
        print(f"processing test request for {model.name} with {type(previous_result)} arguments")
        return [
            {
                "filename": "test_image.jpg",
                "boxes": [
                    {
                        "box": {
                            "topX": 0.078,
                            "topY": 0.068,
                            "bottomX": 0.86,
                            "bottomY": 0.56
                        },
                        "label": "test_label",
                        "score": 1.0,
                        "topN": [
                            {
                                "label": "test_label",
                                "score": 1.0,
                            },
                        ],
                    }
                ]
            }
        ]

    except ValueError as error:
        raise ProcessInferenceResultError("An error occurred while processing the request") from error
