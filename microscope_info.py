import json
import requests
from custom_exceptions import (
    OpenApiError
)

methods = [
    "getVersion",
    "getFieldOfView",
    "getZoomDirect",
    "getFocusDirect",
]

api_url = "http://192.168.0.101/"
params = {"id": 6969}
headers = {'Content-Type': 'application/json'}

def post_request(api_url, method, params, headers):
    url = f"{api_url}?jsonrpc=2.0&method={method}&id={params['id']}"

    data = json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "id": params['id'],
    })

    try:
        resp = requests.post(url, data=data, headers=headers)
        print(resp.text)
        return resp.json()
    except OpenApiError as e:
        print(f"Request Error: {e}")


def get_microscope_configuration():
    config = {}
    for method in methods:
        resp = post_request(api_url, method, params, headers)
        config[method] = resp["result"]
    return json.dumps(config)


if __name__ == "__main__":
    try:
        config = get_microscope_configuration()
        if config:
            print(config)
    except OpenApiError as e:
        print(f"Error: {e}")
