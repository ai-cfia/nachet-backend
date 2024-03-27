import unittest
import model_inference.inference as inference, random

import asyncio


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
        result = asyncio.run(inference.process_inference_results(data=[data], imageDims=[100, 100]))


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
        result = asyncio.run(inference.process_inference_results(data=[data], imageDims=[100, 100]))


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

        random.seed(3)

        test_result = []
        label_occurences = {}

        for box in boxes:
            rgb = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            if box["label"] not in label_occurences:
                label_occurences[box["label"]] = rgb
                test_result.append(rgb)
            else:
                test_result.append(label_occurences[box["label"]])
        colors = []

        result = asyncio.run(inference.process_inference_results(data=[data], imageDims=[100, 100]))

        for box in result[0]["boxes"]:
            colors.append(box["color"])

        self.assertEqual(test_result, colors)

    def test_process_inference_error(self):
        boxes = [
            {"box": self.box1, "score": 10, "label": "box1"},
            {"box": self.box2, "score": 10, "label": "box2"}
        ]

        data = {
            "totalBoxes": 2
        }

        with self.assertRaises(inference.ProcessInferenceResultError):
            asyncio.run(inference.process_inference_results(data=[data], imageDims=[100, 100]))

        data ={
            "boxes": boxes,
            "totalBoxes": 2
        }

        with self.assertRaises(inference.ProcessInferenceResultError):
            asyncio.run(inference.process_inference_results(data=[data], imageDims=100))

        data ={
            "boxes": None,
            "totalBoxes": 2
        }

        with self.assertRaises(inference.ProcessInferenceResultError):
            asyncio.run(inference.process_inference_results(data=[data], imageDims=[100, 100]))
