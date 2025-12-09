from abc import ABC, abstractmethod
 


class IGetProceedingsService(ABC):


    @abstractmethod
    def get_proceedings(self):
        pass