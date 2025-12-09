import logging
from pathlib import Path
from logging import FileHandler
from zoneinfo import ZoneInfo
from datetime import datetime, timedelta
import asyncio

from app.application.dto.HoyPathsDto import HoyPathsDto


class ColombiaFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt=fmt, datefmt=datefmt)

    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=ZoneInfo("America/Bogota"))
        return dt

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()


def setup_logger(log_path: Path):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        logger.handlers.clear()

    log_path.parent.mkdir(parents=True, exist_ok=True)

    file_handler = FileHandler(log_path, encoding="utf-8")
    stream_handler = logging.StreamHandler()

    formatter = ColombiaFormatter(
        format='%(asctime)s - %(levelname)s - [%(module)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'  # formato clásico con hora Colombia
    )

    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


# start_logger modificado para test
async def start_logger():
    logger = logging.getLogger(__name__)
    # Simulamos que la fecha "anterior" es ayer para forzar el cambio
    fecha_actual = (datetime.now(ZoneInfo("America/Bogota")) - timedelta(days=1)).date()

    while True:
        await asyncio.sleep(2)  # cada 2 segundos para pruebas
        nueva_fecha = datetime.now(ZoneInfo("America/Bogota")).date()

        if nueva_fecha != fecha_actual:
            logger.info("📅 Cambio de día detectado. Reiniciando archivo de log.")
            paths = HoyPathsDto.build().model_dump()
            setup_logger(paths["logs_file"])  # Log inicial
            logger.info("Nuevo archivo de log configurado.")
            fecha_actual = nueva_fecha
            break  # salimos en la prueba