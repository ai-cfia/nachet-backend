# :microscope: nachet-backend 🌱

## High level sequence diagram

```mermaid
sequenceDiagram

  title: High Level Sequence Diagram 1.0.0
  actor Client
  participant frontend
  participant backend
  participant EndpointAPI
  participant AzureStorageAPI

Client->>+frontend: getDirectoriesList()
frontend->>+backend: HTTP POST req.
backend->>+AzureStorageAPI: get_blobs()
AzureStorageAPI-->>-backend: blobListObject
backend-->>frontend: directories list res.
frontend-->>Client: display directories
Client->>frontend: handleInference()
frontend->>backend: HTTP POST req.
backend->>+AzureStorageAPI: upload_image(image)
AzureStorageAPI-->>-backend: imageBlobObject
backend->>+EndpointAPI: get_inference_result(image)
EndpointAPI-->>-backend: inference res.
backend->>backend: process inf. result
backend-->>frontend: inference res.
frontend-->>-Client: display inference res.
backend->>+AzureStorageAPI: (async) upload_inference_result(json)
```

**Details**

- The backend was built with the [Quart](http://pgjones.gitlab.io/quart/) framework
- Quart is an asyncio reimplementation of Flask
- All HTTP requests are handled in `app.py` in the root folder
- Azure Storage API calls are handled in the `azure_storage_api/azure_Storage_api.py
- Inference results from model endpoint are directly handled in `model_inference/inference.py`

****

### RUNNING NACHET-BACKEND FROM DEVCONTAINER
When you are developping, you can run the program while in the devcontainer by using this command:
```
hypercorn -b :8080 app:app
```

### RUNNING NACHET-BACKEND AS A DOCKER CONTAINER
If you want to run the program as a Docker container (e.g., for production), use:
```
docker build -t nachet-backend .
docker run -p 8080:8080 -v $(pwd):/app nachet-backend
```

### TESTING NACHET-BACKEND
To test the program, use this command:
```
python -m unittest discover -s tests
```

****
### ENVIRONMENT VARIABLES
Start by making a copy of `.env.template` and renaming it `.env`. For the backend to function, you will need to add the missing values:

* **NACHET_AZURE_STORAGE_CONNECTION_STRING**: Connection string to access external storage (Azure Blob Storage).
* **NACHET_MODEL_ENDPOINT_REST_URL**: Endpoint to communicate with deployed model for inferencing.
* **NACHET_MODEL_ENDPOINT_ACCESS_KEY**: Key used when consuming online endpoint.
* **NACHET_DATA**: Url to access nachet-data repository
* **NACHET_HEALTH_MESSAGE**: Health check message for the server.
* **NACHET_MAX_CONTENT_LENGTH**: Set the maximum size of the file that can be uploaded to the backend. Needs to be the same size as the `client_max_body_size` [value](https://github.com/ai-cfia/howard/blob/dedee069f051ba743122084fcb5d5c97c2499359/kubernetes/aks/apps/nachet/base/nachet-ingress.yaml#L13) set from the deployment in Howard.

****
### DEPLOYING NACHET
If you need help deploying Nachet for your own needs, please contact us at cfia.ai-ia.acia@inspection.gc.ca.
