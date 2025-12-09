

from pathlib import Path
import shutil
from app.domain.interfaces.IBulkUploadService import IBulkUploadService
from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.repositories.CargaMasivaCJRepository import CargaMasivaCJRepository
import os
import json
from datetime import datetime
import math  
import logging

import time
class BulkUploadService(IBulkUploadService):
    logger = logging.getLogger(__name__)

    def __init__( self, db: IDataBase, repository:CargaMasivaCJRepository):
        self.db= db
        self.repository = repository


    def _unificar_ndjson(self):
        """
        Convierte todos los archivos .ndjson dentro de /app/output/jsons
        a un .json con el mismo nombre, en formato de arreglo.
        """
        base_dir = Path("/app/output")
        base_path = os.path.join(base_dir, "jsons")

        if not os.path.exists(base_path):
            print(f"❌ Carpeta no encontrada: {base_path}")
            return

        # Buscar todos los archivos .ndjson en la carpeta
        archivos_ndjson = [
            f for f in os.listdir(base_path) if f.endswith(".ndjson")
        ]

        if not archivos_ndjson:
            print("⚠️ No se encontraron archivos .ndjson.")
            return

        for archivo in archivos_ndjson:
            ruta_ndjson = os.path.join(base_path, archivo)

            # Crear nombre de salida .json
            nombre_base = archivo.replace(".ndjson", "")
            ruta_json = os.path.join(base_path, f"{nombre_base}.json")

            registros = []

            # Leer NDJSON línea por línea
            with open(ruta_ndjson, "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if not linea:
                        continue
                    try:
                        registros.append(json.loads(linea))
                    except json.JSONDecodeError:
                        print(f"⚠️ Línea inválida en {archivo}: {linea}")

            # Guardar JSON normal
            with open(ruta_json, "w", encoding="utf-8") as f:
                json.dump(registros, f, ensure_ascii=False, indent=4)

            print(f"✅ Convertido: {ruta_json} ({len(registros)} registros)")


    # def carga_masiva(self):
    #     """
    #     Lee archivos NDJSON desde output/jsons,
    #     limpia la propiedad 'ubicacion' solo para CEJ_PERU,
    #     convierte línea por línea a JSON string
    #     y hace inserción masiva.
    #     """
    #     conn = None
    #     try:
    #         base_dir = Path("/app/output")
    #         base_path = os.path.join(base_dir, "jsons")

    #         if not os.path.exists(base_path):
    #             raise FileNotFoundError(f"No existe carpeta: {base_path}")

    #         resultados = {}

    #         # Ahora usamos archivos NDJSON
    #         archivos = {
    #             "CEJ_PERU": "actuaciones.ndjson",
    #             "CEJ_ACTORES": "sujetos.ndjson"
    #         }

    #         conn = self.db.acquire_connection()

    #         for tipo, filename in archivos.items():
    #             file_path = os.path.join(base_path, filename)

    #             if not os.path.exists(file_path):
    #                 resultados[tipo] = f"Archivo no encontrado: {file_path}"
    #                 continue

    #             registros = []

    #             # ---------------------------
    #             # 📌 LEER NDJSON (línea por línea)
    #             # ---------------------------
    #             with open(file_path, "r", encoding="utf-8") as f:
    #                 for linea in f:
    #                     linea = linea.strip()
    #                     if not linea:
    #                         continue

    #                     try:
    #                         obj = json.loads(linea)
    #                     except json.JSONDecodeError:
    #                         self.logger.error(f"⚠️ Línea inválida en {filename}: {linea}")
    #                         continue

                  
    #                     registros.append(obj)

    #             # ---------------------------
    #             # 📌 Convertir lista de objetos a NDJSON string
    #             # ---------------------------
    #             ndjson_string = "\n".join(
    #                 json.dumps(r, ensure_ascii=False)
    #                 for r in registros
    #             )

    #             # ---------------------------
    #             # 📌 Insertar masivo
    #             # ---------------------------
    #             insertado = self.repository.insert_masivo(conn, tipo, ndjson_string)

    #             if insertado:
    #                 self.logger.info(f"✅ Insert masivo exitoso para {tipo}")
    #             else:
    #                 self.logger.error(f"❌ Falló inserción para {tipo}")

    #         return resultados

    #     except Exception as e:
    #         self.logger.error(f"❌ Error inesperado en carga_masiva: {e}")

    #     finally:
    #         if conn:
    #             self.db.release_connection(conn)

            

    def carga_masiva(self):
        """
        Busca la carpeta con la fecha actual dentro de output/jsons,
        lee los archivos JSON y ejecuta el procedimiento de cargue masivo.
        Además, limpia los datos de CJ_ACTORES y elimina la propiedad 'ubicacion'
        de todos los registros de CEJ_PERU antes de insertar.
        """
        conn = None
        try:
            self._unificar_ndjson()

            time.sleep(60)   # duerme 5 segundos
      
            base_dir = Path("/app/output")
            base_path = os.path.join(base_dir, "jsons")

            if not os.path.exists(base_path):
                raise FileNotFoundError(f"No existe carpeta para la fecha: {base_path}")

            resultados = {}

            archivos = {
                "CEJ_PERU": "actuaciones.json",
                "CEJ_ACTORES": "sujetos.json"
            }

            conn = self.db.acquire_connection()

            for tipo, filename in archivos.items():
                file_path = os.path.join(base_path, filename)

                if not os.path.exists(file_path):
                    resultados[tipo] = f"Archivo no encontrado: {file_path}"
                    continue

                with open(file_path, "r", encoding="utf-8") as f:
                    json_content = json.load(f)

                # Convertir a string para insertarlo
                json_content = json.dumps(json_content, ensure_ascii=False)

                # Insert masivo
                insertado = self.repository.insert_masivo(conn, tipo, json_content)

                if insertado:
                    self.logger.info(f"✅ Insert masivo exitoso para {tipo}")
                else:
                    self.logger.error(f"❌ Falló inserción para {tipo}")

            return resultados

        except Exception as e:
            self.logger.error(f"❌ Error inesperado en carga_masiva: {e}")

        finally:

            try:
                json_dir = Path("/app/output/jsons")

                if json_dir.exists():
                    for item in json_dir.iterdir():
                        if item.is_file():
                            item.unlink()  # eliminar archivo
                        elif item.is_dir():
                            shutil.rmtree(item)  # eliminar carpeta y su contenido

                    self.logger.info("🧹 Carpeta jsons limpiada correctamente.")

            except Exception as cleanup_error:
                self.logger.error(f"⚠ Error al limpiar la carpeta jsons: {cleanup_error}")

            if conn:
                self.db.release_connection(conn)


    # def carga_masiva(self):
    #     """
    #     Recorre las carpetas de output/jsons/actuaciones y sujetos,
    #     carga TODOS los archivos JSON individuales, los une en un solo
    #     JSON por cada tipo y ejecuta el procedimiento de carga masiva.

    #     Además elimina la propiedad 'ubicacion' solamente en CEJ_PERU.
    #     """
    #     conn = None
    #     try:
    #         base_dir = Path("/app/output/jsons")

    #         carpetas = {
    #             "CEJ_PERU": "actuaciones",
    #             "CEJ_ACTORES": "sujetos"
    #         }

    #         resultados = {}
    #         conn = self.db.acquire_connection()

    #         for tipo, carpeta in carpetas.items():

    #             carpeta_path = base_dir / carpeta

    #             if not carpeta_path.exists():
    #                 resultados[tipo] = f"Carpeta no encontrada: {carpeta_path}"
    #                 continue

    #             data_unificada = []

    #             # 🔄 Recorrer todos los .json de la carpeta
    #             for archivo in carpeta_path.glob("*.json"):
    #                 try:
    #                     with open(archivo, "r", encoding="utf-8") as f:
    #                         contenido = json.load(f)

    #                         if isinstance(contenido, list):
    #                             data_unificada.extend(contenido)
    #                         else:
    #                             data_unificada.append(contenido)

    #                 except Exception as e:
    #                     self.logger.error(f"❌ Error leyendo {archivo}: {e}")

    #             # 🧹 Quitar "ubicacion" solo en CEJ_PERU (actuaciones)
    #             if tipo == "CEJ_PERU":
    #                 for item in data_unificada:
    #                     if isinstance(item, dict):
    #                         item.pop("ubicacion", None)

    #             # Convertir a string antes del insert
    #             json_string = json.dumps(data_unificada, ensure_ascii=False)

    #             insertado = self.repository.insert_masivo(conn, tipo, json_string)

    #             if insertado:
    #                 self.logger.info(f"✅ Insert masivo exitoso para {tipo}")
    #             else:
    #                 self.logger.error(f"❌ Falló la inserción para {tipo}")

    #         return resultados

    #     except Exception as e:
    #         self.logger.error(f"❌ Error inesperado en carga_masiva: {e}")

    #     finally:
    #         if conn:
    #             self.db.release_connection(conn)
