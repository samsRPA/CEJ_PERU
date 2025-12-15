import os
import time
import glob
import json
import logging
from datetime import datetime
import mimetypes
import shutil
import subprocess

import pypandoc



import shutil
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from app.domain.interfaces.IDownloadService import IDownloadService
from app.domain.interfaces.IS3Manager import IS3Manager
from app.infrastucture.database.repositories.DocumentsRepository import DocumentsRepository


class DownloadService(IDownloadService):
    def __init__(self,S3_manager:IS3Manager,repository: DocumentsRepository):
        self.logger = logging.getLogger(__name__)
        self.S3_manager = S3_manager
        
        self.repository=repository


    async def extract_case_records(self,driver, radicado, cod_despacho_rama,conn,download_dir):
        temp_dir=None
        try:
            resoluciones = []
            consecutive_map = {}

            worker_id = os.environ.get("HOSTNAME", "worker_default")
            temp_dir = os.path.join(download_dir, f"temp_{worker_id}_{radicado}")
            os.makedirs(temp_dir, exist_ok=True)
            self.logger.info(f"📁 Carpeta temporal creada: {temp_dir}")

            # 🔽 Cambiar destino de descargas para este radicado
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": temp_dir
            })
            ubicacion = None
            try:
                ubicacion_label = driver.find_element(
                    By.XPATH,
                    "//div[contains(@class,'celdaGrid') and normalize-space()='Ubicación:']"
                )
                ubicacion_value = ubicacion_label.find_element(By.XPATH, "following-sibling::div[1]")
                ubicacion = ubicacion_value.text.strip()

                self.logger.info(f"📌 Ubicación: {ubicacion}")

            except Exception as e:
                self.logger.error(f"⚠️ No se encontró ubicación → {e}")


            # 👇 Forzar visibilidad de todos los paneles
            driver.execute_script("""
                document.querySelectorAll("div[id^='pnlSeguimiento']").forEach(e => e.style.display = 'block');
            """)
            
            # 👇 Esperar hasta que todos los paneles estén cargados y visibles
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[id^='pnlSeguimiento']"))
                )
                bloques = driver.find_elements(By.CSS_SELECTOR, "div[id^='pnlSeguimiento']")
                self.logger.info(f"📄 Se encontraron {len(bloques)} paneles de seguimiento visibles.")
            except Exception as e:
                self.logger.error(f"⚠️ Advertencia: no se pudieron cargar todos los paneles a tiempo → {e}")

            
            os.makedirs(download_dir, exist_ok=True)
            
            
            for idx, bloque in enumerate(bloques, start=1):
                self.logger.info(f"\n🔹 Procesando panel {idx}...")
                data = {}

                # --- Función segura para obtener texto ---
                def safe_text(xpath):
                    try:
                        return bloque.find_element(By.XPATH, xpath).text.strip()
                    except:
                        return None

                fecha_res = None
                downloadable = None
                msg= None  # 🔥 Reset al inicio del ciclo
                # --- Verificar si hay mensaje de no visualización ---
 
                try:
                    msg = bloque.find_element(By.CSS_SELECTOR, "div.sinResol.divResolImpar").text.strip()
                    
                   
                    
                    
                    if msg:  
                        self.logger.info("el archivo no es descargable")
                        downloadable = False
                    
                    if "Los escritos no se pueden visualizar" in msg:
                        print("⚠️ Los escritos no se pueden visualizar por este medio.")
                        fecha_res = safe_text(".//div[div[contains(.,'Fecha de Ingreso:')]]/div[@class='fleft']")
                        downloadable = False

                    elif "El documento de la resolución no se encuentra anexado. Favor de ponerse en contacto con el personal del Juzgado o el Secretario del Juzgado." in msg:
                        print("⚠️ El documento de la resolución no está anexado.")
                        fecha_res = safe_text(".//div[div[contains(.,'Fecha de Resolución:')]]/div[@class='fleft']")
                        downloadable = False
                    else:
                        fecha_res = safe_text(".//div[div[contains(.,'Fecha de Resolución:')]]/div[@class='fleft']")
                        downloadable = True

                except NoSuchElementException:
                    
                    # 🔹 Si no hay mensaje de advertencia, intentamos ambas fechas
                    fecha_res = safe_text(".//div[div[contains(.,'Fecha de Resolución:')]]/div[@class='fleft']")
                    if not fecha_res:
                        fecha_res = safe_text(".//div[div[contains(.,'Fecha de Ingreso:')]]/div[@class='fleft']")
                        downloadable = False
                    else:
                        downloadable = True


                # --- Convertir formatos de fecha ---
                fecha_formateada = None
                fecha_registro_tyba = "00-00-0000 00:00:00"
                fecha_obj=None
                if fecha_res:
                    fecha_res = fecha_res.strip()
                    try:
                        # Caso 1 → "30/10/2018"
                        if len(fecha_res) == 10:
                            fecha_obj = datetime.strptime(fecha_res, "%d/%m/%Y")
                            fecha_formateada = fecha_obj.strftime("%d-%m-%Y")
                            fecha_registro_tyba = fecha_obj.strftime("%d-%m-%Y 00:00:00")

                        # Caso 2 → "16/08/2019 11:37"
                        elif len(fecha_res) > 10:
                            fecha_obj = datetime.strptime(fecha_res, "%d/%m/%Y %H:%M")
                            fecha_formateada = fecha_obj.strftime("%d-%m-%Y")
                            fecha_registro_tyba = fecha_obj.strftime("%d-%m-%Y %H:%M:%S")

                    except ValueError:
                        self.logger.warning(f"⚠️ No se pudo parsear la fecha: {fecha_res}")

                # --- Datos base del registro ---
                data["radicado"] = radicado
               # data["ubicacion"]= ubicacion
                data["cod_despacho_rama"] = cod_despacho_rama
                data["fecha"] = fecha_formateada
                data["actuacion_rama"] = safe_text(".//div[contains(.,'Acto:')]/following-sibling::div[contains(@class,'fleft')]")
                data["anotacion_rama"] = safe_text(".//div[div[contains(.,'Sumilla:')]]/div[@class='fleft']")
                data["origen_datos"] = "CEJ_PERU"
                data["fecha_registro_tyba"] = fecha_registro_tyba

                resoluciones.append(data)
               
               

                if downloadable:
                    dataToCheck = {
                        
                            "FECHA_NOTIFICACION": fecha_obj,
                            "RADICACION": radicado,
                        }
                    
                    key = f"{radicado}-{fecha_formateada}"
                    if key in consecutive_map:
                        consecutivo = consecutive_map[key]
                        consecutive_map[key] = consecutivo + 1
                    else:
                        max_consecutivo = await self.repository.get_max_consecutive(conn, dataToCheck)
                        consecutivo = max_consecutivo + 1
                        consecutive_map[key] = consecutivo + 1
                    
                    ruta_S3 = f"{fecha_formateada}_{radicado}_{consecutivo}"
                    print(f"concecutivo: {consecutivo}")
                    dataToCheck["CONSECUTIVO"] = consecutivo

                    
                  
                    exists = await self.repository.exists_document(conn, dataToCheck)

                    if exists:
                        continue
                  

                    
                    
                    is_insert_s3 = await self._download_records( bloque, driver, fecha_formateada, radicado, data, consecutivo, temp_dir,consecutive_map)

                    if is_insert_s3:
                        insert_bd= await self.repository.insert_document(conn,fecha_formateada,radicado,consecutivo,ruta_S3,"",data["origen_datos"],"pdf",fecha_registro_tyba)
                        if insert_bd:
                            self.logger.info(f" ✅ Insertado en control autos rama 1 con radicado {radicado}, fecha {fecha_formateada} y consecutivo {consecutivo} ")


                
                
            await conn.commit()
            #             # ==========================================================
            # #   📝 GUARDAR RESOLUCIONES EN ARCHIVO GLOBAL NDJSON (SEGURO)
            # # ==========================================================

            try:
                jsons_dir = "/app/output/jsons"
                os.makedirs(jsons_dir, exist_ok=True)

                file_path = f"{jsons_dir}/actuaciones.ndjson"

                # Append línea por línea (no se corrompe)
                with open(file_path, "a", encoding="utf-8") as f:
                    for r in resoluciones:
                        f.write(json.dumps(r, ensure_ascii=False) + "\n")

                self.logger.info(f"📝 {len(resoluciones)} actuaciones agregadas a {file_path}")

            except Exception as e:
                self.logger.error(f"❌ Error guardando NDJSON: {e}")

            # --- Guardar datos en JSON ---
    #--- Guardar datos en JSON ---
           # json_path = os.path.join("/app/output/jsons", "actuaciones.json")
            # #json_path = os.path.join("output/jsons", "actuaciones.json")
            # # Si el archivo existe, cargar datos previos
            # if os.path.exists(json_path):
            #     with open(json_path, "r", encoding="utf-8") as f:
            #         try:
            #             existing_data = json.load(f)
            #             if not isinstance(existing_data, list):
            #                 existing_data = []
            #         except json.JSONDecodeError:
            #             existing_data = []
            # else:
            #     existing_data = []

            # # Agregar los nuevos datos
            # existing_data.extend(resoluciones)  # resoluciones es tu lista nueva

            # # Guardar todo de nuevo
            # with open(json_path, "w", encoding="utf-8") as f:
            #     json.dump(existing_data, f, indent=4, ensure_ascii=False)

           
        #     carpeta = "/app/output/jsons/actuaciones"
        #     os.makedirs(carpeta, exist_ok=True)

        #     output_path = f"{carpeta}/{radicado}.json"

        #         # Guardar JSON directo
        #     with open(output_path, "w", encoding="utf-8") as f:
        #         json.dump(resoluciones, f, ensure_ascii=False, indent=4)

        #     self.logger.info(f"✅ JSON creado: {output_path}")

        #    # self.logger.info(f"📁 JSON guardado en: {json_path}")
        #     return resoluciones
        except Exception as e:
            self.logger.error(f"Error : {e}")
        finally:
            # 🔚 Limpieza final de la carpeta temporal
            if os.path.exists(temp_dir) and temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
                self.logger.info(f"🧹 Carpeta temporal eliminada al finalizar: {temp_dir}")

        return resoluciones

    async def _download_records(self, bloque, driver, fecha_formateada, radicado, data, consecutivo, temp_dir, consecutive_map):
        """
        Descarga, renombra, sube a S3 y limpia el archivo.
        Usa una carpeta temporal ya creada por radicado y por worker.
        """
        try:
            enlace = bloque.find_element(By.CSS_SELECTOR, "a.aDescarg")
            driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", enlace)
            time.sleep(0.3)

            try:
                enlace.click()
                self.logger.info("📥 Documento descargado con click normal.")
            except Exception:
                self.logger.info("⚠️ Click interceptado, aplicando click por JavaScript...")
                driver.execute_script("arguments[0].click();", enlace)
                self.logger.info("✅ Documento descargado con click JS.")

            time.sleep(2)

            lista = glob.glob(os.path.join(temp_dir, "*"))
            if not lista:
                self.logger.warning(f"⚠️ No hay archivos descargados para radicado {radicado}.")
                # 🔙 Revertir incremento de consecutivo si no hubo descarga
                if consecutive_map and f"{radicado}-{fecha_formateada}" in consecutive_map:
                    consecutive_map[f"{radicado}-{fecha_formateada}"] -= 1
                    self.logger.info(f"↩️ Revertido consecutivo en mapa para {radicado}-{fecha_formateada}")
                return False

            archivo_reciente = max(lista, key=os.path.getctime)

            while archivo_reciente.endswith(".crdownload"):
                time.sleep(0.5)
                lista = glob.glob(os.path.join(temp_dir, "*"))
                if not lista:
                    continue
                archivo_reciente = max(lista, key=os.path.getctime)

            mime_type, _ = mimetypes.guess_type(archivo_reciente)
            self.logger.info(f"📄 Tipo MIME detectado: {mime_type}")
            if mime_type != "application/pdf":
                pdf_temporal = os.path.splitext(archivo_reciente)[0] + ".pdf"
                convertido = await self.convert_to_pdf(archivo_reciente, pdf_temporal)
                if convertido:
                    self.logger.info(f"🧩 Archivo convertido a PDF correctamente: {pdf_temporal}")
                    os.remove(archivo_reciente)
                    archivo_reciente = pdf_temporal
                else:
                    self.logger.warning(f"⚠️ No se pudo convertir {archivo_reciente} a PDF.")
                    os.remove(archivo_reciente)
                    # 🔙 Revertir incremento de consecutivo si falla conversión
                    if consecutive_map and f"{radicado}-{fecha_formateada}" in consecutive_map:
                        consecutive_map[f"{radicado}-{fecha_formateada}"] -= 1
                        self.logger.info(f"↩️ Revertido consecutivo en mapa para {radicado}-{fecha_formateada}")
                    return False

            nuevo_nombre = f"{fecha_formateada}_{radicado}_{consecutivo}.pdf"
            nuevo_path = os.path.join(temp_dir, nuevo_nombre)
            os.rename(archivo_reciente, nuevo_path)
            self.logger.info(f"✅ Archivo renombrado como: {nuevo_nombre}")

            subida_ok = self.S3_manager.uploadFile(nuevo_path)
            if not subida_ok:
                self.logger.error("❌ Fallo al subir el archivo a S3.")
                # 🔙 Revertir incremento si falla subida
                if consecutive_map and f"{radicado}-{fecha_formateada}" in consecutive_map:
                    consecutive_map[f"{radicado}-{fecha_formateada}"] -= 1
                    self.logger.info(f"↩️ Revertido consecutivo en mapa para {radicado}-{fecha_formateada}")
                return False

            return True

        except NoSuchElementException:
            self.logger.info("ℹ️ No hay enlace de descarga en este panel.")
            # 🔙 Revertir incremento si no hay enlace
            if consecutive_map and f"{radicado}-{fecha_formateada}" in consecutive_map:
                consecutive_map[f"{radicado}-{fecha_formateada}"] -= 1
                self.logger.info(f"↩️ Revertido consecutivo en mapa para {radicado}-{fecha_formateada}")
            return False

        except Exception as e:
            self.logger.error(f"❌ Error al intentar descargar: {e}")
            # 🔙 Revertir incremento en cualquier error
            if consecutive_map and f"{radicado}-{fecha_formateada}" in consecutive_map:
                consecutive_map[f"{radicado}-{fecha_formateada}"] -= 1
                self.logger.info(f"↩️ Revertido consecutivo en mapa para {radicado}-{fecha_formateada}")
            return False






    async def convert_to_pdf(self, input_path: str, output_path: str) -> bool:
        try:
            subprocess.run([
                "libreoffice", "--headless", "--convert-to", "pdf", "--outdir",
                os.path.dirname(output_path), input_path
            ], check=True)
            self.logger.info(f"✅ Archivo convertido correctamente con LibreOffice: {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Error al convertir {input_path} con LibreOffice: {e}", exc_info=True)
            return False


