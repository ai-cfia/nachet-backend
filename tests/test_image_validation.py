import unittest
import base64
import json
import asyncio

from app import app
from io import BytesIO
from PIL import Image
from unittest.mock import patch, Mock


class TestImageValidation(unittest.TestCase):
    def setUp(self):
        self.test_client = app.test_client()

        self.img_byte_array = BytesIO()
        image = Image.new('RGB', (150, 150), 'blue')
        self.image_header = "data:image/PNG;base64,"
        image.save(self.img_byte_array, 'PNG')

    def test_real_image_validation(self):
        data = base64.b64encode(self.img_byte_array.getvalue())
        data = data.decode('utf-8')

        response = asyncio.run(
            self.test_client.post(
                '/image-validation',
                headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                },
                data= str.encode(json.dumps({'image': self.image_header + data})),
            ))

        data = json.loads(asyncio.run(response.get_data()))

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(data[0], str)

    def test_invalid_header_image_validation(self):
        data = base64.b64encode(self.img_byte_array.getvalue()).decode('utf-8')

        response = asyncio.run(
            self.test_client.post(
                '/image-validation',
                headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                },
                data= str.encode(json.dumps({'image':"data:image/," + data})),
            ))

        data = json.loads(asyncio.run(response.get_data()))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data[0], 'Invalid file header')

    @patch("PIL.Image.open")
    def test_invalid_extension(self, mock_open):

        mock_image = Mock()
        mock_image.format = "md"

        mock_open.return_value = mock_image

        data = base64.b64encode(self.img_byte_array.getvalue()).decode('utf-8')

        response = asyncio.run(
            self.test_client.post(
                '/image-validation',
                headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                },
                data= str.encode(json.dumps({'image': self.image_header + data})),
            ))

        data = json.loads(asyncio.run(response.get_data()))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data[0], 'Invalid file extension')

    @patch("PIL.Image.open")
    def test_invalid_size(self, mock_open):
        mock_image = Mock()
        mock_image.size = [2000, 2000]
        mock_image.format = "PNG"

        mock_open.return_value = mock_image

        data = base64.b64encode(self.img_byte_array.getvalue()).decode('utf-8')

        response = asyncio.run(
            self.test_client.post(
                '/image-validation',
                headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                },
                data= str.encode(json.dumps({'image': self.image_header + data})),
            ))

        data = json.loads(asyncio.run(response.get_data()))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data[0], 'Invalid file size')

    @patch("PIL.Image.open")
    def test_rezisable_error(self, mock_open):
        mock_image = Mock()
        mock_image.size = [1080, 1080]
        mock_image.format = "PNG"
        mock_image.thumbnail.side_effect = IOError("error can't resize")

        mock_open.return_value = mock_image

        data = base64.b64encode(self.img_byte_array.getvalue()).decode('utf-8')

        response = asyncio.run(
            self.test_client.post(
                '/image-validation',
                headers={
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                },
                data= str.encode(json.dumps({'image': self.image_header + data})),
            ))

        data = json.loads(asyncio.run(response.get_data()))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data[0], 'Invalid file not resizable')

if __name__ == '__main__':
    unittest.main()