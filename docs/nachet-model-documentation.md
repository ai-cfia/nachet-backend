# Nachet Interactive Models

## Executive Summary

Nachet Interactive uses various models to detect seeds. Documentation is
essential to keep track of their features. The models can perform different
tasks, including Image Classification, Image Segmentation, and Object Detection.

## Task

Nachet Interactive models' perform the following tasks:

|Task|Action|Input/Output|
|:--|:--|:-----|
|[Classification](https://huggingface.co/tasks/image-classification) | This task involves assigning a single label or class to each image the model receives. | The input for the classification models is an image, and the output is a prediction of the class it belongs to. |
|[Object Detection](https://huggingface.co/tasks/object-detection) | Identify and locate an object belonging to a specific class within an image. |The object detection models take an image as an input and output the image with a label and a box around the detected object. |
|[Segmentation](https://huggingface.co/tasks/image-segmentation) | Segmentation is the task of dividing images into different parts, where each pixel in the image is mapped to an object. It includes instance segmentation, panoptic segmentation, and semantic segmentation.| The segmentation models take an image as input and return an image divided into objects. |

> As of today (2024-02-22), no model uses segmentation. To know more about each
> task, click on the task to follow the link to their hugging face page. To know
> more about AI tasks in general: [Hugging Face
> Tasks](https://huggingface.co/tasks)

## List of models

|Model|Full name|Task|Active|Accuracy|
|--|--|:--:|:--:|:--:|
|Nachet-6seeds | m-14of15seeds-6seedsmag | Object Detection | Yes | - |
|Seed-detector | seed-detector-1 |  Object Detection | Yes | - |
|Swin | swinv1-base-dataaugv2-1 | Classification | Yes | - |

## Return value of models

```json
{
    "filename": "tmp/tmp_file_name",
    "boxes": [
        {"box": {
                "topX": 0.0,
                "topY": 0.0,
                "bottomX": 0.0,
                "bottomY": 0.0
            },
        "label": "top_label_name",
        "score": 0.912,
        "topResult": [
            {
                "score": 0.912
                "label": "top_label_name",
            },
            {
                "score": 0.053
                "label": "seed_name",
            },
            {
                "score": 0.0029
                "label": "seed_name",
            },
            {
                "score": 0.005
                "label": "seed_name",
            },
            {
                "score": 0.001
                "label": "seed_name",
            }
        ],
        "overlapping": false,
        "overlappingIndices": 0
        },
    ],
    "labelOccurrence": {
        "seed_name": 1,
    },
    "totalBoxes": 1
}
```

## Different ways of calling models

### Header

The endpoint can host multiple models, so specifying the model name in the
header is necessary to avoid errors.

```python
# Header for every model should be:
headers = {
    'Content-Type': 'application/json',
    'Authorization': ('Bearer ' + endpoint_api_key),
    'azureml-model-deployment': model_name
}
```

### Body

The body structure difference is based on the model tasks. A classification
model can only classify one seed in an image, whereas an object detection model
can detect if the image contains one or multiple seeds. It remains to be
determined whether a segmentation model requires a different body structure.
[See task](#task)

```python
# Object Detection model
# Example: Nachet-6seeds and seed-detector
body = {
    'input_data': {
        'columns': ['image'],
        'index': [0],
        'data': [image_bytes],
    }
}

# Classification model
# Example: Swin
body = b64encode(image)
```

## Error from models

A list of common error models returns to the backend.

> To access the error from the model, go to the model endpoint in azure and look
> for the logs : CFIA/ACIA/workspace/endpoint/model/logs

|Error|Model|Reason|Message|
|--|--|--|--|
|ValueError| Swin |Incorrect image source|Must be a valid url starting with `http://` or `https://`, a valid path to an image file, or a base64 encoded string|

## Pipeline and model data

In order to dynamically build the pipeline in the backend from the model, the
following data structure was designed. For now, the pipelines will have two keys for their names (`model_name`, `piepline_name`) to support the frontend code until it is changed to get the name of the pipeline with the correct key. 

```json
{
    "version": "0.1.0",
    "date": "2024-02-26",
    "pipelines":
    [
        {
            "models": ["model 1", "model 2"],
            "model_name": "Model(Pipeline) 1",
            "pipeline_name": "Pipeline 1",
            "created_by": "creator name",
            "creation_date": "2024-01-01",
            "version": "1",
            "description": "",
            "job_name": "",
            "dataset": "",
            "metrics": [],
            "identifiable": []
        }
    ],
    "models":
    [
        {
            "task": "object-detection",
            "api_call_function": "function_key",
            "endpoint": "endpoint",
            "api_key": "key",
            "infeference functions": "function_key",
            "content-type": "application/json",
            "deployment_platform": {"azure": "azureml-model-deployment"},
            "endpoint_name": "endpoint-name",
            "model_name": "model name",
            "created_by": "creator name",
            "creation_date": "2024-01-01",
            "version": "1",
            "description": "",
            "job_name": "",
            "dataset": "",
            "metrics": [],
            "identifiable": []
        }
    ]
}
```
