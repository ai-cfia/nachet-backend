from tests.test_azure_storage_api import TestMountContainerFunction, TestGetBlob, testGetPipeline
from tests.test_inference_request import TestInferenceRequest, TestQuartHealth

# a = TestMountContainerFunction()
# a.test_mount_existing_container()
# a.test_mount_nonexisting_container_create()
# a.test_mount_nonexisting_container_no_create()

# b = TestGetBlob()
# b.test_get_blob_successful()
# b.test_get_blob_unsuccessful()

# c = testGetPipeline()
# c.test_get_pipeline_info_unsuccessful()
# c.test_get_pipeline_info_successful()

d = TestInferenceRequest()
d.setUp()
d.test_inference_request_successful()
d.test_inference_request_unsuccessfull()
d.test_inference_request_missing_argument()
d.test_inference_request_wrong_pipeline_name()
d.test_inference_request_wrong_header()
d.tearDown()

# e = TestQuartHealth()
# e.test_health()