

import concurrent
from pathlib import Path
import shutil
from app.domain.interfaces.IBulkUploadService import IBulkUploadService

import os
import json
from datetime import datetime
import math  
import logging

from app.domain.interfaces.IS3Manager import IS3Manager
import datetime


class BulkUploadService(IBulkUploadService):

    def __init__(self, s3_manager: IS3Manager):
        self.s3_manager = s3_manager
        self.logger = logging.getLogger(__name__)


    def upload_folders(self, base_path: str) -> None:
        self.upload_logs_folder(base_path)
  



        

    def upload_logs_folder(self, base_path) -> None:
        """
        Sube los archivos del directorio base_path/logs a S3.
        - Si el archivo es .csv → va a la carpeta /logs/ en S3
        - Si el archivo es .json → va a la carpeta /resumen/ en S3
        - Ignora los archivos que correspondan a la fecha actual (según su nombre).
        - Elimina localmente los archivos subidos con éxito (excepto los del día actual).
        """
        base_path = str(base_path)
        logs_path = os.path.join(base_path, "logs")

        if not os.path.exists(logs_path):
            self.logger.error(f"La ruta {logs_path} no existe.")
            return

        self.logger.info(f"🗂️ Iniciando subida de carpeta de logs: {logs_path}")

        # Fecha actual (para detectar archivos del día)
        hoy = datetime.datetime.now().strftime("%d-%m-%Y")

        # Contadores para resumen
        subidos = 0
        errores = 0
        ignorados = 0

        for file_name in os.listdir(logs_path):
            file_path = os.path.join(logs_path, file_name)

            if not os.path.isfile(file_path):
                continue

            # Ignorar archivos del día actual
            if hoy in file_name:
                self.logger.info(f"⏩ Ignorando archivo del día actual: {file_name}")
                ignorados += 1
                continue

            # Detectar tipo de archivo
            extension = os.path.splitext(file_name)[1].lower()

            if extension == ".csv":
                s3_folder = "logs"
            else:
                self.logger.warning(f"⚠️ Tipo de archivo no soportado: {file_name}")
                continue

            s3_key = f"{self.s3_manager.prefix}/{s3_folder}/{file_name}".replace("\\", "/")

            self.logger.info(f"📤 Subiendo {file_path} → s3://{self.s3_manager.bucketName}/{s3_key}")

            try:
                success = self.s3_manager.uploadFile(file_path, s3_key)

                if success:
                    self.logger.info(f"✅ Subido correctamente: {file_name}")
                    subidos += 1
                    # Eliminar el archivo después de subirlo exitosamente
                    try:
                        os.remove(file_path)
                        self.logger.info(f"🗑️ Archivo eliminado localmente: {file_name}")
                    except Exception as e:
                        self.logger.error(f"⚠️ No se pudo eliminar {file_name}: {e}")
                else:
                    self.logger.error(f"❌ Falló la subida: {file_name}")
                    errores += 1

            except Exception as e:
                self.logger.error(f"💥 Error inesperado subiendo {file_name}: {e}")
                errores += 1

        self.logger.info(
            f"🎯 Subida completa de 'logs': "
            f"{subidos} subidos y eliminados, {errores} errores, {ignorados} ignorados ({hoy})."
        )