import stat
import unittest
import asyncio
import os
import base64

from app import app, json


class TestNewBatchImport(unittest.TestCase):
    def setUp(self):
        self.test_client = app.test_client()
        self.container_name = "a427278e-28df-428f-8937-ddeeef44e72f"
        self.nb_pictures = 1
        self.folder_name = None
        
    def tearDown(self):
        if(self.folder_name != None):
            response = asyncio.run(
                self.test_client.post(
                    '/del',
                    headers={
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    json={
                        "container_name": self.container_name,
                        "folder_name": self.folder_name
                    })
            )
            if(response.status_code == 200):
                self.folder_name = None
        self.test_client = None

    def test_new_batch_import_successfull(self):

        response = asyncio.run(
            self.test_client.post(
                '/new-batch-import',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "container_name": self.container_name,
                    "nb_pictures": self.nb_pictures
                })
        )
        
        self.assertEqual(response.status_code, 200)
        result_json = json.loads(asyncio.run(response.get_data()))
        self.assertTrue(result_json.get("session_id")!=None)
        
        self.folder_name = result_json.get("session_id")

    def test_new_batch_import_missing_arguments_error(self):
        """
        Test if a request with missing arguments return an error
        """
        expected = ("APIErrors while initiating the batch import: missing request arguments: either container_name or nb_pictures is missing")

        response = asyncio.run(
            self.test_client.post(
                '/new-batch-import',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "nb_pictures": self.nb_pictures
                })
        )
        result_json = json.loads(asyncio.run(response.get_data()))
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(result_json[0], expected)
        
    def test_new_batch_import_wrong_nb_pictures(self):
        """
        Test if a request with a wrong argument return an error
        """
        expected = ("APIErrors while initiating the batch import: wrong request arguments: either container_name or nb_pictures is wrong")

        response = asyncio.run(
            self.test_client.post(
                '/new-batch-import',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "container_name": "",
                    "nb_pictures": self.nb_pictures
                })
        )
        result_json = json.loads(asyncio.run(response.get_data()))
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(result_json[0], expected)

        response = asyncio.run(
            self.test_client.post(
                '/new-batch-import',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "container_name": self.container_name,
                    "nb_pictures": "1"
                })
        )
        result_json = json.loads(asyncio.run(response.get_data()))
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(result_json[0], expected)
        
        response = asyncio.run(
            self.test_client.post(
                '/new-batch-import',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "container_name": self.container_name,
                    "nb_pictures": 0
                })
        )
        result_json = json.loads(asyncio.run(response.get_data()))
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(result_json[0], expected)
        
class TestUploadBatchImport(unittest.TestCase):
    def setUp(self):
        self.test_client = app.test_client()
        self.container_name = "a427278e-28df-428f-8937-ddeeef44e72f"
        self.nb_pictures = 1
        
        response = asyncio.run(
            self.test_client.post(
                '/new-batch-import',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "container_name": self.container_name,
                    "nb_pictures": self.nb_pictures
                })
        )
        
        result_json = json.loads(asyncio.run(response.get_data()))
        self.folder_name = result_json.get("session_id")
        
        self.seed_name = "Ambrosia artemisiifolia"
        self.zoom_level = None
        self.nb_seeds = None
        current_dir = os.path.dirname(__file__)
        image_path = os.path.join(current_dir, 'img/1310_1.png')
        self.image_header = "data:image/PNG;base64,"
        with open(image_path, 'rb') as image_file:
            self.image_src = base64.b64encode(image_file.read()).decode('utf-8')
        self.image = self.image_header + self.image_src
        
    def tearDown(self):
        if(self.folder_name != None):
            response = asyncio.run(
                self.test_client.post(
                    '/del',
                    headers={
                        "Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*",
                    },
                    json={
                        "container_name": self.container_name,
                        "folder_name": self.folder_name
                    })
            )
            if(response.status_code == 200):
                self.folder_name = None
        # does delete folder also delete pictures ?
        self.test_client = None
        
    def test_upload_picture_successfull(self):
        response = asyncio.run(
            self.test_client.post(
                '/upload-picture',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "container_name": self.container_name,
                    "session_id": self.folder_name,
                    "seed_name": self.seed_name,
                    "zoom_level": self.zoom_level,
                    "nb_seeds": self.nb_seeds,
                    "image": self.image
                })
        )
        self.assertEqual(response.status_code, 200)
        result_json = json.loads(asyncio.run(response.get_data()))[0]
        print(result_json)
        
    def test_upload_picture_missing_arguments_error(self):
        """
        Test if a request with missing arguments return an error
        """
        expected = ("APIErrors while uploading pictures: missing request arguments: either seed_name, session_id, container_name or image is missing")

        response = asyncio.run(
            self.test_client.post(
                '/upload-picture',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "container_name": self.container_name,
                    # missing session_id
                    "seed_name": self.seed_name,
                    "zoom_level": self.zoom_level,
                    "nb_seeds": self.nb_seeds,
                    "image": self.image 
                })
        )
        result_json = json.loads(asyncio.run(response.get_data()))
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(result_json[0], expected)
    
    def test_upload_picture_wrong_arguments_error(self):
        """
        Test if a request with wrong arguments return an error
        """
        expected = ("APIErrors while uploading pictures: wrong request arguments: either seed_name, session_id, container_name or image is wrong")

        response = asyncio.run(
            self.test_client.post(
                '/upload-picture',
                headers={
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*",
                },
                json={
                    "container_name": "", # wrong container_name
                    "session_id": self.folder_name,
                    "seed_name": self.seed_name,
                    "zoom_level": self.zoom_level,
                    "nb_seeds": self.nb_seeds,
                    "image": self.image 
                })
        )
        result_json = json.loads(asyncio.run(response.get_data()))
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(result_json[0], expected)
        