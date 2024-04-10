from model.swin import request_inference_from_swin
from model.seed_detector import request_inference_from_seed_detector
from model.test import request_inference_from_test
from model.six_seeds import request_inference_from_nachet_6seeds

request_function = {
    "swin": request_inference_from_swin,
    "seed_detector": request_inference_from_seed_detector,
    "test": request_inference_from_test,
    "nachet_6seeds": request_inference_from_nachet_6seeds
}
