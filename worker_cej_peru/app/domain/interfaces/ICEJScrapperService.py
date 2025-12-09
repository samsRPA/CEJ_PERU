from abc import ABC, abstractmethod

class ICEJScrapperService(ABC):


    @abstractmethod
    async def scrapper(self,radicado):
        pass