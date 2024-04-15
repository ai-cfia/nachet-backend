from model.swin import request_inference_from_swin
from model.seed_detector import request_inference_from_seed_detector
from model.test import request_inference_from_test
from model.six_seeds import request_inference_from_nachet_6seeds

request_function = {
    "swin-endpoint": request_inference_from_swin,
    "seed-detector": request_inference_from_seed_detector,
    "test": request_inference_from_test,
    "nachet-6seeds": request_inference_from_nachet_6seeds
}
