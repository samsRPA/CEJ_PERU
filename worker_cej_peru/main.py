import logging
import asyncio

from pathlib import Path
import sys
from app.dependencies.Dependencies import Dependencies
from app.infrastucture.config.Settings import load_config
from app.application.dto.HoyPathsDto import HoyPathsDto

from app.infrastucture.config.LogsConfig import setup_logger, start_logger

  # ============ Configuración de logging ============
def setup_logger(log_path: Path):
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [%(module)s] %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
               
            ],
        )


   # ============ Configuración de logging ============
logger= logging.getLogger(__name__)

async def main():
    paths = HoyPathsDto.build().model_dump()
    setup_logger(paths["logs_file"])
    config = load_config()
    dependency = Dependencies()
    dependency.settings.override(config)
    consumer = dependency.rabbitmq_consumer()
    db = dependency.data_base()
    try:
        await db.connect()
        # await asyncio.gather(
        await consumer.startConsuming()
        #     start_logger()
        # )
    except Exception as e:
        logger.exception("❌ Error durante la ejecución principal", exc_info=e)
    finally:
        try:
            if db.is_connected:
                await db.close_connection()
        except Exception as error:
            logger.exception(f"⚠️ No se pudo cerrar la DB correctamente: {error}")
  



if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.exception("Interrupción manual del programa.")
