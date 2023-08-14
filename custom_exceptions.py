class DeleteDirectoryRequestError(Exception):
    pass

class ListDirectoriesRequestError(Exception):
    pass

class InferenceRequestError(Exception):
    pass

class GenerateHashError(Exception):
    pass

class MountContainerError(Exception):
    pass

class ContainerNameError(Exception):
    pass

class ConnectionStringError(Exception):
    pass

class GetBlobError(Exception):
    pass

class UploadImageError(Exception):
    pass

class UploadInferenceResultError(Exception):
    pass

class GetFolderUUIDError(Exception):
    pass

class FolderListError(Exception):
    pass

class ProcessInferenceResult(Exception):
    pass