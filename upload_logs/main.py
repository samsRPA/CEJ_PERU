import logging

import asyncio
from pathlib import Path
import sys
from app.dependencies.Dependencies import Dependencies
from app.infrastucture.config.Settings import load_config
from app.application.dto.HoyPathsDto import HoyPathsDto
 



        # ============ Configuración de logging ============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s] %(message)s',
)


logger = logging.getLogger(__name__)
async def main():
    
    paths = HoyPathsDto.build().model_dump()
 

    config = load_config()
    dependency = Dependencies()
    dependency.settings.override(config)
    upload_logs = dependency.bulk_upload_service()
 
    try:
   
        upload_logs.upload_folders(paths["base_output"])
        
    except Exception as e:
        logger.exception("❌ Error durante la ejecución principal", exc_info=e)
 
  
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.exception("Interrupción manual del programa.")