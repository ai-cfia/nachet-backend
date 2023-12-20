import json
import requests
from custom_exceptions import OpenApiError
from dotenv import load_dotenv
import os

load_dotenv()

methods = [
    "getVersion",       # Returns microscope version
    "getFieldOfView",   # Returns FoV as an int value (μm)
    "getZoomDirect",    # Returns current zoom as string hex value
    "getFocusDirect",   # Returns current focus as string hex value
    "getContrast",      # Returns position of the Contrast slider
    "getSaturation",    # Returns position of the Saturation slider
    "getSharpness"      # Returns position of the Sharpness slider
]

MICROSCOPE_URL = os.getenv("MICROSCOPE_URL")
params = {"id": 6969}
headers = {'Content-Type': 'application/json'}

def post_request(MICROSCOPE_URL, method, params, headers):
    url = f"{MICROSCOPE_URL}?jsonrpc=2.0&method={method}&id={params['id']}"

    data = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "id": params['id'],
    })

    try:
        resp = requests.post(url, data=data, headers=headers)
        return resp.json()
    except OpenApiError as e:
        print(f"Request Error: {e}")

def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def get_microscope_configuration():
    config = {}
    for method in methods:
        resp = post_request(MICROSCOPE_URL, method, params, headers)
        result = resp["result"]

        # Check if the response is in hexadecimal and convert it
        if isinstance(result, str) and is_hex(result):
            result = int(result, 16)

        config[method] = result

    return json.dumps(config, indent=4)


if __name__ == "__main__":
    try:
        config = get_microscope_configuration()
        if config:
            print(config)
    except OpenApiError as e:
        print(f"Error: {e}")
