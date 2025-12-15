from abc import ABC, abstractmethod


class IBulkUploadService(ABC):

    @abstractmethod
    def upload_folders(self, base_path: str):
        pass