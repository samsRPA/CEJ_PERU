from abc import ABC, abstractmethod


class IBulkUploadService(ABC):

    @abstractmethod
    def carga_masiva():
        pass