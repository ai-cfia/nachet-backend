# nachet-backend

## High level sequence diagram
![SD_1 drawio (2)](https://github.com/ai-cfia/nachet-backend/assets/19809069/272f37dc-f4ec-449b-ba82-950c54b9f856)

### Details

- The backend was built with the [Quart](http://pgjones.gitlab.io/quart/)
framework
- Quart is an asyncio reimplementation of Flask
- All HTTP requests are handled in `app.py` in the root folder
- Azure Storage API calls are handled in the `azure_storage_api/azure_Storage_api.py`
- Inference results from model endpoint are directly handled in
`model_inference/inference.py`

****

### RUNNING NACHET-BACKEND FROM DEVCONTAINER
When you are developping, you can run the program while in the devcontainer
by using this command:
```bash
hypercorn -b :8080 app:app
```

### RUNNING NACHET-BACKEND AS A DOCKER CONTAINER
If you want to run the program as a Docker container (e.g., for production),
use:
```bash
docker build -t nachet-backend .
docker run -p 8080:8080 -v $(pwd):/app nachet-backend
```

### TESTING NACHET-BACKEND
To test the program, use this command:
```bash
python -m unittest discover -s tests
```

****
### ENVIRONMENT VARIABLES
Start by making a copy of `.env.template` and renaming it `.env`. For the
backend to function, you will need to add the missing values:

* **NACHET_AZURE_STORAGE_CONNECTION_STRING**: Connection string to access
external storage (Azure Blob Storage).
* **NACHET_MODEL_ENDPOINT_REST_URL**: Endpoint to communicate with deployed
model for inferencing.
* **NACHET_MODEL_ENDPOINT_ACCESS_KEY**: Key used when consuming online endpoint.
* **NACHET_DATA**: Url to access nachet-data repository
* **NACHET_HEALTH_MESSAGE**: Health check message for the server.

****
### DEPLOYING NACHET
If you need help deploying Nachet for your own needs, please contact us
at cfia.ai-ia.acia@inspection.gc.ca.
