from model.swin import request_inference_from_swin
from model.seed_detector import request_inference_from_seed_detector
from model.test import request_inference_from_test
from model.six_seeds import request_inference_from_nachet_6seeds

request_function = {
    "local-seed-detector-rcnn": request_inference_from_seed_detector,
    "local-swin-15-spp": request_inference_from_swin,
    "local-swin-22-spp": request_inference_from_swin,
    "swin-22-spp": request_inference_from_swin,
    "swinv1-base-dataaugv2-1": request_inference_from_swin,
    "seed-detector-1": request_inference_from_seed_detector,
    "swinv1-base-dataaugv2-2": request_inference_from_swin,
    "seed-detector-rcnn-1": request_inference_from_seed_detector,
    "test": request_inference_from_test,
    "m-14of15seeds-6seedsmag": request_inference_from_nachet_6seeds
}
