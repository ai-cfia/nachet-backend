import unittest
import asyncio

from model_inference.inference import process_inference_results, ProcessInferenceResultError, Color


class TestInferenceProcessFunction(unittest.TestCase):
    def setUp(self):
        self.box1 = {
            "topX": 1,
            "topY": 1,
            "bottomX": 40,
            "bottomY": 40,
        }
        self.box2 = {
            "topX": 20,
            "topY": 20,
            "bottomX":60,
            "bottomY": 40,
        }

    def test_process_inference_overlap_results(self):
        boxes = [
            {"box": self.box1, "score": 20, "label": "box1"},
            {"box": self.box2, "score": 10, "label": "box2"}
        ]
        data = {
            "boxes": boxes,
            "totalBoxes": 2
        }
        result = asyncio.run(process_inference_results(data=[data], imageDims=[100, 100]))


        self.assertFalse(result[0]["boxes"][0]["overlapping"])
        self.assertTrue(result[0]["boxes"][1]["overlapping"])

    def test_process_inference_overlap_score_results(self):
        boxes = [
            {"box": self.box1, "score": 10, "label": "box1"},
            {"box": self.box2, "score": 10, "label": "box2"}
        ]
        data = {
            "boxes": boxes,
            "totalBoxes": 2
        }
        result = asyncio.run(process_inference_results(data=[data], imageDims=[100, 100]))


        self.assertFalse(result[0]["boxes"][0]["overlapping"])
        self.assertFalse(result[0]["boxes"][1]["overlapping"])

    def test_generate_color(self):
        boxes = [
            {"box": self.box1, "score": 10, "label": "box1"},
            {"box": self.box2, "score": 30, "label": "box2"},
            {"box": self.box1, "score": 10, "label": "box2"},
        ]

        data = {
            "boxes": boxes,
            "totalBoxes": 1
        }

        color_res = set()
        colors = list(Color("yellow").range_to(Color("green"), len(boxes)))

        expected_result = set([c.get_hex() for i, c in enumerate(colors) if boxes[i]["label"] != boxes[i - 1]["label"]])
        result = asyncio.run(process_inference_results(data=[data], imageDims=[100, 100], colors=("yellow", "green")))

        for box in result[0]["boxes"]:
            color_res.add(box["color"])

        self.assertEqual(color_res, expected_result)

    def test_process_inference_error(self):
        boxes = [
            {"box": self.box1, "score": 10, "label": "box1"},
            {"box": self.box2, "score": 10, "label": "box2"}
        ]

        data = {
            "totalBoxes": 2
        }

        with self.assertRaises(ProcessInferenceResultError):
            asyncio.run(process_inference_results(data=[data], imageDims=[100, 100]))

        data ={
            "boxes": boxes,
            "totalBoxes": 2
        }

        with self.assertRaises(ProcessInferenceResultError):
            asyncio.run(process_inference_results(data=[data], imageDims=100))

        data ={
            "boxes": None,
            "totalBoxes": 2
        }

        with self.assertRaises(ProcessInferenceResultError):
            asyncio.run(process_inference_results(data=[data], imageDims=[100, 100]))
