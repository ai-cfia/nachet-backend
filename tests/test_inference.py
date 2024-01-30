import unittest
import model_inference.inference as inference

import asyncio

box1 = {
    "topX": 1,
    "topY": 1,
    "bottomX": 40,
    "bottomY": 40,
}
box2 = {
    "topX": 20,
    "topY": 20,
    "bottomX":60,
    "bottomY": 40,
}

class TestInferenceProcessFunction(unittest.TestCase):
    def test_process_inference_overlap_results(self):
        boxes = [
            {"box": box1, "score": 20, "label": "box1"},
            {"box": box2, "score": 10, "label": "box2"}
        ]
        data = {
            "boxes": boxes,
            "totalBoxes": 2
        }
        result = asyncio.run(inference.process_inference_results(data=[data], imageDims=[100, 100]))


        self.assertFalse(result[0]["boxes"][0]["overlapping"])
        self.assertTrue(result[0]["boxes"][1]["overlapping"])

        print(result)
        # self.assertEqual(result, None)
    def test_process_inference_overlap_score_results(self):
        boxes = [
            {"box": box1, "score": 10, "label": "box1"},
            {"box": box2, "score": 10, "label": "box2"}
        ]
        data = {
            "boxes": boxes,
            "totalBoxes": 2
        }
        result = asyncio.run(inference.process_inference_results(data=[data], imageDims=[100, 100]))


        self.assertFalse(result[0]["boxes"][0]["overlapping"])
        self.assertFalse(result[0]["boxes"][1]["overlapping"])

        # self.assertEqual(result, None)
        


