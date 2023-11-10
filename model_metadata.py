import os
import re
import json
import yaml
from dotenv import load_dotenv
from azure.ai.ml import MLClient, Input
from azure.ai.ml.entities import Model
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential

load_dotenv()

NACHET_SUBSCRIPTION_ID = os.getenv("NACHET_SUBSCRIPTION_ID")
NACHET_RESOURCE_GROUP = os.getenv("NACHET_RESOURCE_GROUP")
NACHET_WORKSPACE = os.getenv("NACHET_WORKSPACE")

def generate_model_metadata():
    """
    Retrieves deployed online_endpoints and generates metadata json 
    """

    model_metadata = []
    model_json = {}

    ml_client = MLClient(DefaultAzureCredential(), NACHET_SUBSCRIPTION_ID, NACHET_RESOURCE_GROUP, NACHET_WORKSPACE)

    # Retrieve all endpoints containing "nachet"
    endpoints = ml_client.online_endpoints.list()
    nachet_endpoints = [endpoint for endpoint in endpoints if 'nachet' in endpoint.name.lower()]

    ep = nachet_endpoints[0]

    # Retrieve online_deployment
    deployment = ml_client.online_deployments.get(endpoint_name=ep.name, name=list(ep.traffic.keys())[0])

    # Retrieve deployment's model (from filePath)
    model_filepath = deployment.model
    pattern = re.compile(r"models/([^/]+)/versions/(\d+)")
    match = pattern.search(model_filepath)
    if match:
        model_name = match.group(1)  
        model_version = match.group(2)  
    else:
        print("No match found")

    # Retrieve the job object from model
    model = ml_client.models.get(name=model_name, version=model_version)
    job = ml_client.jobs.get(name=model.job_name)

    # Because json.dumps(job) returns an empty json, use the dump() method from the Job class to write contents of job object to YAML file
    job.dump(dest='output.yaml')

    # Read the YAML file and convert it to a dictionary
    with open('output.yaml', 'r') as file:
        job_data = yaml.safe_load(file)

    return job_data
        

if __name__ == "__main__":
    job_json = generate_model_metadata()
    print(job_json["component"]) 