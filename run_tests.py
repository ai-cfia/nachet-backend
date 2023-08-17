from tests.test_azure_storage_api import *

a = TestMountContainerFunction()
a.test_mount_existing_container()
a.test_mount_nonexisting_container_create()
a.test_mount_nonexisting_container_no_create()

b = TestGetBlob()
b.test_get_blob_successful()
b.test_get_blob_unsuccessful()