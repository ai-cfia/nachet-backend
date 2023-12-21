import os
import json
import uuid
import logging
import requests
from dotenv import load_dotenv
from custom_exceptions import MicroscopeQueryError

load_dotenv()

methods_str  = os.getenv("METHODS", "[]")
METHODS = json.loads(methods_str)
MICROSCOPE_URL = os.getenv("MICROSCOPE_URL")
params = {"id": int(uuid.uuid4())}
HEADERS = {'Content-Type': 'application/json'}

def post_request(MICROSCOPE_URL, method, params, headers=HEADERS):
    url = f"{MICROSCOPE_URL}?jsonrpc=2.0&method={method}&id={params['id']}"

    data = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "id": params['id'],
    })

    try:
        resp = requests.post(url, data=data, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        logging.error(f"Request Error: {e}")
        raise MicroscopeQueryError(f"MicroscopeQueryError: {e}") from e

def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def get_microscope_configuration(METHODS):
    config = {}
    for method in METHODS:
        try:
            resp = post_request(MICROSCOPE_URL, method, params, HEADERS)
            result = resp["result"]

            # Check if the response is in hexadecimal and convert it
            if isinstance(result, str) and is_hex(result):
                result = int(result, 16)

            config[method] = result
            
        except MicroscopeQueryError as mqe:
            config[method] = None
            logging.error(f"MicroscopeQueryError: {mqe}")

    return config


if __name__ == "__main__":
    try:
        config = get_microscope_configuration(METHODS)
        if config:
            print(config)
    except requests.RequestException as e:
        raise MicroscopeQueryError(f"OpenApiError: {e}") from e
