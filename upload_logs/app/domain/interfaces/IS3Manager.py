from abc import ABC, abstractmethod

class IS3Manager(ABC):
    @abstractmethod
    def uploadFile(self, file_path: str, s3_key: str):
        pass

   