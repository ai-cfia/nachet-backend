# Inference Request with n-models pipelines

## Executive summary

Nachet Interactive is currently working on improving the effectiveness and user
experience of detecting regulated seeds. To achieve this goal, the AI Lab is
implementing various AI models that can perform tasks such as seed detection in
an image or seed classification. These models can work together or independently
to enhance the accuracy of the results. When combined with other models, each
model builds upon the work of the previous one to deliver the final outcome.
This process is defined as a pipeline of models.

Each model produces a result based on its inference, which is the process of
machine learning to generate predictions from a dataset. The purpose of this
document is to provide a technical design for the implementation of the
inference request with multiple pipelines where the pipeline to run against is
selected by a parameter.

## Glossary

### Pipelines
Pipelines are defined as a set of models that follow each other, where the output of
one model is used as input for the next models, and so on. A pipeline contains from 1 to n
models.

#### Pipelines flowchart 1.0.0
```mermaid
flowchart LR

A{Pipeline entry point}-->|user input|SB1-->F{Pipeline exit point}-->|"last model
output"|G>"return
result.json to user"]

subgraph SB1[In pipeline]
    direction TB

    B(model 01)-->|"model output
    send to the next one"|C(model 02)-->|can have n models|D(n models)

end
```

### Models
A model is an AI model that is a part of a pipeline. A model accepts images as
input and returns JSON as output. Generally, this JSON contains the coordinates
of objects in the source image, that the model may pass along to feed the next
step of the pipeline.


### Model from Frontend
On the frontend interface, a pipeline will be called a model, because the user
will not be aware of the difference. From the user's perspective, they send data
to a model and receive the result.

*Suggestion: we could call the pipeline a method if we don't want to mix terms.*

# Sequence Diagram for inference request 1.0.0

```mermaid
sequenceDiagram

    actor Client
    participant Frontend
    participant Backend
    participant Blob storage
    participant Model

    Note over Backend,Blob storage: initialisation
    Backend-)Backend: before_serving()
    Backend-)Backend: get_pipelines_models()
    alt
    Backend-)Blob storage: HTTP POST req.
    Blob storage--)Backend: return pipelines_models.json
    else
    Backend-)Frontend: error 400 No pipeline found
    end
    Note over Backend,Blob storage: end of initialisation
   
    Client->>Frontend: applicationStart()
    Frontend-)Backend: HTTP POST req.
    Backend-)Backend: get_pipelines_names()
    Backend--)Frontend: Pipelines names res.
    Note left of Backend: return pipelines names and metadata

    Frontend->>Client: application is ready
    Client-->>Frontend: client ask action from specific pipeline
    Frontend-)Backend: HTTP POST req.
    Backend-)Backend: inference_request(pipeline_name, folder_name, container_name, imageDims, image)
    alt missing argument
        Backend--)Frontend: Error 400 missing arguments
    else no missing argument
        Backend-)Backend: mount_container(connection_string(Environnement Variable, container_name))
        Backend-)Blob storage: HTTP POST req.
        Blob storage--)Backend: container_client
        
        Backend-)Backend: upload_image(container_client, folder_name, image_bytes, hash_value)
        Backend-)Blob storage: HTTP POST req.
        Blob storage--)Backend: blob_name

        Backend-)Backend: get_blob(container_client, blob_name)
        Backend-)Blob storage: HTTP POST req.
        Blob storage--)Backend: blob

        loop for every model in pipeline
            note over Backend, Blob storage: Header construction
            Note over Backend,Blob storage: {"Content-Type": "application/json", <br>"Authorization": ("Bearer " + endpoint_api_key),}
            Backend-)Backend: urllib.request.Request(endpoint_url, body, header)
            Backend-)Model: HTTP POST req.
            Model--)Backend: Result res.
            alt next model is not None
                note over Backend, Blob storage: restart the loop process
                Backend-)Backend: record_result(model, result)
                Backend-)Blob storage: HTTP POST req.
                note over Backend, Blob storage: record the result produced by the model

            end
        end
        
        par Backend to Frontend
            Backend-)Backend: inference.process_inference_results(data, imageDims)
            Backend--)Frontend: Processed result res.
        and Backend to Blob storage
            Backend-)Backend: upload_inference_result(container_client, folder_name, result_json_string, hash_value)
            Backend-)Blob storage: HTTP POST req.
        end
    end
    Frontend--)Client: display result
```

![footer_for_diagram](https://github.com/ai-cfia/nachet-backend/assets/96267006/cf378d6f-5b20-4e1d-8665-2ba65ed54f8e)

### Input and Output for inference request
The inference request will process the following parameters:

|Key parameters | Expected Value|
--|--
model_name | The name of the pipeline
folder_name | The folder where the image is uploaded in the user's container
container_name | The user's container
imageDims | The dimension of the image
image | The image encoded in b64 (ASCII)

Note that since the information is received from the frontend, the model_name is
an abstraction for a pipeline.

The inference request will return a list with the following information:
|key parameters | hierarchy Levels | Return Value |
--|--|--
Boxes | 0 | Contains all the boxes returned by the inference request
Box | 1 | Contains all the information of one seed in the image
totalBoxes | 1 | Boxes total number
label | 2 | Contains the top label for the seed
score | 2 | Contains the top score for the seed
topResult | 2 | Contains the top 5 scores for the seed
overlapping | 2 | Contains a boolean to tell if the box overlap with another one
overlappingIndices | 2 | Contains the index of the overlapping box

**topResult** contains the top 5 predictions of the models:
```json
"topResult": [
    {
        'label': seed_name,
        'score': 0,75
    }
    {
        'label': seed_name,
        'score': 0,18
    }
    {
        'label': seed_name,
        'score': 0,05
    }
    {
        'label': seed_name,
        'score': 0,019
    }
    {
        'label': seed_name,
        'score': 0,001
    }
]
```

