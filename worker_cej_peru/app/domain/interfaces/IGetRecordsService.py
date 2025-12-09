


from abc import ABC, abstractmethod

class IGetRecordsService(ABC):
    
    @abstractmethod
    def get_records_by_Code(self,driver, wait, radicado):
        pass
    
    @abstractmethod   
    def get_records_by_Filters(self,driver, wait,distrito_judicial,instancia, especialidad,annio,num_expediente):
       pass

    # @abstractmethod
    # def get_actors(self,wait, radicado):
    #    pass