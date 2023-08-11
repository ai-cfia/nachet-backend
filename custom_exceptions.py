class MountContainerError(ValueError):
    pass

class UploadImageError(ValueError):
    pass

class UploadInferenceResultsError(ValueError):
    pass

class GetBlobError(ValueError):
    pass

class GetFolderUUIDError(ValueError):
    pass

class DeleteFolderError(ValueError):
    pass

class FolderListError(ValueError):
    pass

class GenerateHashError(ValueError):
    pass

class ProcessInferenceResults(ValueError):
    pass

class InferenceRequestError(ValueError):
    pass

class FolderListRequestError(ValueError):
    pass

class DeleteFolderRequestError(ValueError):
    pass