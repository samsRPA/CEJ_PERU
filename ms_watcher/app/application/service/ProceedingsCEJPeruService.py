

from app.domain.interfaces.IGetProceedingsService import IGetProceedingsService

import logging
from app.domain.interfaces.IRabbitMQProducer import IRabbitMQProducer
from app.application.dto.ProceedingsDto import ProceedingsDto
from app.domain.interfaces.IProceedingsCEJPeruService import IProceedingsCEJPeruService


class ProceedingsCEJPeruService(IProceedingsCEJPeruService):

    logger= logging.getLogger(__name__)
   
    def __init__(self,  getData:IGetProceedingsService, producer: IRabbitMQProducer):
        self.getData = getData
        self.producer= producer
     
    async def getAllProceedings(self):
      
        try:
            
            raw_proceedings = await self.getData.get_proceedings()
            if raw_proceedings:
                self.logger.info(f"✅ Se extrayeron {len(raw_proceedings)} expedientes")
            return raw_proceedings
        except Exception as e:
            self.logger.error(f"❌ Error : {e}")
            raise e
 

    async def publishProceedings(self):
   
            try:
                    
               
                proceedings= await self.getAllProceedings()

                if not proceedings:
                    raise ValueError("No hay radicados para publicar")
                
                for proceeding in proceedings:
                    print(proceeding)
    
                    await self.producer.publishMessage(proceeding.dict())
 
            except Exception as error:
                logging.exception(f"Error al publicar {error}")
                raise error 
       
    
