from abc import ABC, abstractmethod


class IProceedingsCEJPeruService(ABC):



    @abstractmethod
    async def publishProceedings(self,user,password,insert):
        pass