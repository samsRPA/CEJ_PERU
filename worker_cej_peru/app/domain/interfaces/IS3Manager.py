from abc import ABC, abstractmethod

class IS3Manager(ABC):
    
    @abstractmethod
    async def uploadFile(self,filePath):
        pass