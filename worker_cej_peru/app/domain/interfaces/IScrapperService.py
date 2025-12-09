from abc import ABC, abstractmethod


class IScrapperService(ABC):


    @abstractmethod
    async def runScrapper(self):
        pass
