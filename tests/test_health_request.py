import unittest
import asyncio

from app import app

class TestQuartHealth(unittest.TestCase):
    def test_health(self):
        test = app.test_client()

        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            test.get('/health')
        )
        print(response.status_code)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()