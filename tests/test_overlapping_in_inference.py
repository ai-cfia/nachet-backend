import unittest
import asyncio

from model.inference import (
    process_inference_results,
    primary_colors,
    light_colors,
    ProcessInferenceResultError
)

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
        result = asyncio.run(
            process_inference_results(data=[data], imageDims=[100, 100]))


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
        result = asyncio.run(
            process_inference_results(data=[data], imageDims=[100, 100]))


        self.assertFalse(result[0]["boxes"][0]["overlapping"])
        self.assertFalse(result[0]["boxes"][1]["overlapping"])

    def test_generate_color_hex(self):
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

        expected_result = set()
        for i, c in enumerate(primary_colors["hex"][:len(boxes)]):
            if boxes[i]["label"] != boxes[i - 1]["label"]:
                expected_result.add(c)

        result = asyncio.run(
            process_inference_results(data=[data], imageDims=[100, 100]))

        for box in result[0]["boxes"]:
            color_res.add(box["color"])

        self.assertEqual(color_res, expected_result)

    def test_generate_color_rgb(self):
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

        expected_result = set()

        for i, c in enumerate(primary_colors["rgb"][:len(boxes)]):
            if boxes[i]["label"] != boxes[i - 1]["label"]:
                expected_result.add(c)

        result = asyncio.run(
            process_inference_results(
                data=[data], imageDims=[100, 100], color_format="rgb"))

        for box in result[0]["boxes"]:
            color_res.add(box["color"])

        self.assertEqual(color_res, expected_result)

    def test_generate_color_over_set(self):
        boxes = [
            {"box": self.box1, "score": 10, "label": "box1"},
            {"box": self.box2, "score": 30, "label": "box2"},
            {"box": self.box1, "score": 10, "label": "box3"},
            {"box": self.box1, "score": 10, "label": "box4"},
            {"box": self.box1, "score": 10, "label": "box5"},
            {"box": self.box1, "score": 10, "label": "box6"},
            {"box": self.box1, "score": 10, "label": "box7"},
            {"box": self.box1, "score": 10, "label": "box8"},
            {"box": self.box1, "score": 10, "label": "box9"},
            {"box": self.box1, "score": 10, "label": "box10"},
        ]

        data = {
            "boxes": boxes,
            "totalBoxes": 1
        }

        color_res = []
        expected_result = []

        set1 = primary_colors["rgb"]
        set2 = light_colors["rgb"]

        for i, _ in enumerate(boxes):
            if i < len(set1):
                expected_result.append(set1[i])
            else:
                expected_result.append(set2[i-len(set1)])

        result = asyncio.run(
            process_inference_results(
                data=[data], imageDims=[100, 100], color_format="rgb"))

        for box in result[0]["boxes"]:
            color_res.append(box["color"])

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
            asyncio.run(
                process_inference_results(data=[data], imageDims=[100, 100]))

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
            asyncio.run(
                process_inference_results(data=[data], imageDims=[100, 100]))
