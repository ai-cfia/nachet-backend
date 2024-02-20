import base64
import json

from io import BytesIO
from PIL import Image
from unittest import TestCase, main
import requests

"""
In order for the tests to run, the server must be running.
TO DO - Create a mock server to run the tests without the need for the server to be running.
TO DO - Implement test_image for every other checks (size, format, resizable)
TO DO - Implement test_image for every type of image (PNG, JPEG, GIF, BMP, TIFF, WEBP, SVG)
TO DO - 
"""

class test_image_validation(TestCase):
# V1 with server running
    def test_real_image_validation(self):
        image = Image.new('RGB', (150, 150), 'blue')

        # Save the image to a byte array
        img_byte_array = BytesIO()

        image_header = "data:image/PNG;base64,"

        image.save(img_byte_array, 'PNG')

        data = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

        response = requests.post(
            url="http://0.0.0.0:8080/image-validation",
            data= str.encode(json.dumps({'image': image_header + data})),
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            }
        )
        data = json.loads(response.content)

        if isinstance(data[1], str):
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data[0], True)
        else:
            self.assertEqual(response.status_code, 200)

# v2 with server not running
    def test_invalid_header_image_validation(self):
        image = Image.new('RGB', (150, 150), 'blue')

        # Save the image to a byte array
        img_byte_array = BytesIO()

        image_header = "data:image/,"

        image.save(img_byte_array, 'PNG')

        data = base64.b64encode(img_byte_array.getvalue()).decode('utf-8')

        response = requests.post(
            url="http://0.0.0.0:8080/image-validation",
            data= str.encode(json.dumps({'image': image_header + data})),
            headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            }
        )

        data = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data[0], False)
        self.assertEqual(data[1], 'Invalid file header')

if __name__ == '__main__':
    main()