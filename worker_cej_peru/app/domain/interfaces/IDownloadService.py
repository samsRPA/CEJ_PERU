from abc import ABC, abstractmethod

class IDownloadService(ABC):
  

    @abstractmethod
    async def extract_case_records(self,driver, radicado, cod_despacho_rama,conn):
        pass