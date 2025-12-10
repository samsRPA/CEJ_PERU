
import logging
import re
from app.domain.interfaces.ICEJScrapperService import ICEJScrapperService
import glob
import shutil
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException
)
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, ElementNotInteractableException
from datetime import datetime
import os, time
from collections import defaultdict
import os
from datetime import datetime

import json
import pandas as pd

from app.domain.interfaces.ISeleniumManager import ISeleniumManager
from app.domain.interfaces.IFormScrapper import IFormScrapper
from app.domain.interfaces.IDataBase import IDataBase
from app.domain.interfaces.IDownloadService import IDownloadService


class CEJScrapperService(ICEJScrapperService):

    def __init__(self, driver_selenium:ISeleniumManager, url, form_scrapper:IFormScrapper, db: IDataBase, download_service:IDownloadService):
        self.driver_selenium=driver_selenium
        self.url=url
        self.form_scrapper=form_scrapper
        self.db=db
        self.download_service=download_service
        self.logger= logging.getLogger(__name__)
        
    CHROME_MAJOR = 143
    URL = "https://cej.pj.gob.pe/cej/forms/busquedaform.html"
 
    DOWNLOAD_DIR ="/app/output/descargas"
    #DOWNLOAD_DIR ="output/descargas"
        
    def crear_driver(self):
        # Crear carpeta de descargas si no existe
        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

        # Opciones de Chrome
        opts = uc.ChromeOptions()
        opts.add_argument("--start-maximized")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-popup-blocking")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--window-size=1200,900")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
        )

        # ⚙️ Preferencias para descargas automáticas
        prefs = {
            "download.default_directory": self.DOWNLOAD_DIR,              # Ruta donde guardar
            "download.prompt_for_download": False,                   # No preguntar dónde guardar
            "download.directory_upgrade": True,                      # Permitir sobrescribir
            "safebrowsing.enabled": True,                            # Permitir descargas sin alerta
            "profile.default_content_settings.popups": 0,            # Bloquear popups
        }
        opts.add_experimental_option("prefs", prefs)

        # Crear el driver
        driver = uc.Chrome(options=opts, version_main=self.CHROME_MAJOR)

        # Ocultar bandera "webdriver"
        try:
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception:
            pass

        return driver

    async def scrapper(self, case_information):
        driver = None
        conn = None
        try:
            driver = self.crear_driver()
            driver.get(self.url)
            wait = WebDriverWait(driver, 20)
            actions = ActionChains(driver)
            num_expediente = case_information.num_expediente
            nombre_completo=case_information.nombre_completo
            annio = case_information.annio

            is_completed_form = self.form_scrapper.fill_out_form(wait, driver, case_information, actions)
            #conn = await self.db.acquire_connection()
            

            if is_completed_form:
                
                panel_selector = "#divDetalles .divGLRE0, #divDetalles .divGLRE1"

                paneles = driver.find_elements(By.CSS_SELECTOR, panel_selector)
                total = len(paneles)

                self.logger.info(f"🔎 Se encontraron {total} expedientes en la página.")

                for index in range(1, total + 1):

                    # RE-CARGAR la lista de paneles (evita stale element)
                    paneles = driver.find_elements(By.CSS_SELECTOR, panel_selector)
                    panel = paneles[index - 1]

                    self.logger.info("\n==============================")
                    self.logger.info(f"▶️ Procesando expediente #{index}")
                    self.logger.info("==============================")

                    try:
                        # -----------------------------
                        # 1. Extraer radicado y juzgado
                        # -----------------------------
                        elementos_b = panel.find_elements(By.CSS_SELECTOR, ".divNroJuz b")

                        if len(elementos_b) < 2:
                            self.logger.warning("⚠️ No se encontraron <b> necesarios en el panel.")
                            continue

                        radicado = elementos_b[0].text.strip()
                        cod_despacho_rama = elementos_b[1].text.strip()

                        self.logger.info(f"🔎 Radicado: {radicado}")
                        self.logger.info(f"🏛️ Juzgado/Rama: {cod_despacho_rama}")
                        self._extrac_actors(wait, radicado)

                        # -----------------------------
                        # 2. Guardar screenshot
                        # -----------------------------
                        screenshot_path = f"/app/output/img/{radicado}_{num_expediente}.png"
                        #screenshot_path = f"output/img/{radicado}_{num_expediente}.png"
                        driver.save_screenshot(screenshot_path)
                        self.logger.info(f"📸 Captura guardada: {screenshot_path}")

                        # -----------------------------
                        # 3. Guardar JSON
                        # -----------------------------
                        #json_path = "output/base/radicados_update.json"
                        json_path = "/app/output/base/radicados_update.json"
                        radicado_update = {
                            "radicado": radicado,
                            "num_exp": num_expediente,
                            "nombre_completo":nombre_completo,
                            "annio": annio
                        }


                        os.makedirs(os.path.dirname(json_path), exist_ok=True)

                        if not os.path.exists(json_path):
                            with open(json_path, "w", encoding="utf-8") as f:
                                json.dump([radicado_update], f, indent=4, ensure_ascii=False)
                        else:
                            try:
                                with open(json_path, "r", encoding="utf-8") as f:
                                    data = json.load(f)
                            except:
                                data = []

                            data.append(radicado_update)
                            with open(json_path, "w", encoding="utf-8") as f:
                                json.dump(data, f, indent=4, ensure_ascii=False)

                        # -----------------------------
                        # 4. Click botón del panel
                        # -----------------------------
                        boton = panel.find_element(By.CSS_SELECTOR, "form#command button")
                        actions.move_to_element(boton).pause(0.2).click(boton).perform()

                        self.logger.info("🖱️ Botón clicado correctamente.")

                        # Esperar carga
                        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        time.sleep(1.5)

                        # -----------------------------
                        # 5. Procesar panel
                        # -----------------------------
                        await self.download_service.extract_case_records(
                            driver,
                            radicado,
                            cod_despacho_rama,
                            conn,
                            self.DOWNLOAD_DIR
                        )

                        # -----------------------------
                        # 6. Regresar SOLO si NO es el último
                        # -----------------------------
                        if index < total:  
                            try:
                                back_button = wait.until(
                                    EC.element_to_be_clickable((By.CSS_SELECTOR, "img[alt='Regresar a la página anterior']"))
                                )
                                back_button.click()

                                self.logger.info("🔙 Regresando con botón oficial CEJ...")
                                
                                # Esperar recarga del listado
                                wait.until(EC.presence_of_element_located((By.ID, "divDetalles")))
                                time.sleep(1.2)

                            except Exception as e:
                                self.logger.error(f"❌ Falló el botón regresar: {e}")
                        else:
                            self.logger.info("🛑 Última iteración: NO se regresa.")
                            break  # opcional si quieres terminar más rápido

                    except Exception as e:
                        self.logger.warning(f"⚠️ Error procesando el panel #{index}: {e}")
                        continue

            else:
                self.logger.warning("⚠️ No se logro llenar el formulario completo.")













            # if is_completed_form:
            #     #if radicado and cod_despacho_rama:
            #     await self.download_service.extract_case_records(driver, radicado, cod_despacho_rama, conn,self.DOWNLOAD_DIR)
            # else:
            #     self.logger.warning("⚠️ No se pudo extraer radicado o despacho, se omite procesamiento.")

        except Exception as e:
            self.logger.error(f"❌ Error en scrapper: {e}", exc_info=True)
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    self.logger.warning(f"Error cerrando driver: {e}")
                    try:
                        driver.service.stop()
                    except Exception as e2:
                        self.logger.warning(f"Error deteniendo servicio del driver: {e2}")
            if conn:
                try:
                    await self.db.release_connection(conn)
                except Exception as e:
                    self.logger.warning(f"Error liberando conexión DB: {e}")



    def  _extrac_actors(self,wait, radicado):
            try:
                # Esperar el elemento con las partes
                parte_element = wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.partesp"))
                )
                texto = parte_element.text.strip()

                # Extraer los bloques de texto (DEMANDANTE / DEMANDADO)
                patrones = re.findall(r"(DEMANDANTE|DEMANDADO):\s*([^:]+?)(?=(?:DEMANDANTE|DEMANDADO|$))", texto)

                # Convertir a DataFrame directamente
                df = pd.DataFrame(patrones, columns=["TIPO_SUJETO", "NOMBRE_ACTOR"])

                # Limpiar texto y separar demandados múltiples por coma
                df["NOMBRE_ACTOR"] = df["NOMBRE_ACTOR"].str.replace(r"\.$", "", regex=True)
                df = df.assign(NOMBRE_ACTOR=df["NOMBRE_ACTOR"].str.split(","))

                # Expandir los nombres separados por coma (sin usar for)
                df = df.explode("NOMBRE_ACTOR").reset_index(drop=True)
                df["NOMBRE_ACTOR"] = df["NOMBRE_ACTOR"].str.strip()

                # Reemplazar DEMANDANTE por ACTOR
                df["TIPO_SUJETO"] = df["TIPO_SUJETO"].replace({"DEMANDANTE": "ACTOR"})

                # Agregar columnas fijas
                df["RADICADO_RAMA"] = radicado
                df["ORIGEN_DATOS"] = "CEJ_PERU"

                # Reordenar columnas
                df = df[["RADICADO_RAMA", "TIPO_SUJETO", "NOMBRE_ACTOR", "ORIGEN_DATOS"]]

        # # --- ✨ CREAR JSON INDIVIDUAL POR RADICADO ✨ ---

        #         # Ruta final: /app/output/jsons/sujetos/<radicado>.json
        #         carpeta = "/app/output/jsons/"
        #         os.makedirs(carpeta, exist_ok=True)


        #         # Guardar JSON directo
        #         with open(output_path, "w", encoding="utf-8") as f:
        #             json.dump(df.to_dict(orient="records"), f, ensure_ascii=False, indent=4)

        #         self.logger.info(f"✅ JSON creado: {output_path}")
                # ==========================================================
                #   📝 GUARDAR SUJETOS EN ARCHIVO GLOBAL NDJSON (SEGURO)
                # ==========================================================

                try:
                    carpeta = "/app/output/jsons"
                    os.makedirs(carpeta, exist_ok=True)

                    file_path = f"{carpeta}/sujetos.ndjson"

                    # Convertir el DF a registros
                    records = df.to_dict(orient="records")

                    # Escribir cada sujeto en una línea (append seguro)
                    with open(file_path, "a", encoding="utf-8") as f:
                        for r in records:
                            f.write(json.dumps(r, ensure_ascii=False) + "\n")

                    self.logger.info(f"📝 {len(records)} sujetos agregados a {file_path}")

                except Exception as e:
                    self.logger.error(f"❌ Error guardando sujetos: {e}")

                return df

            except TimeoutException:
                self.logger.warning("⚠️ No se encontró el elemento de partes procesales.")
                return pd.DataFrame()
            except Exception as e:
                self.logger.error("❌ Error extrayendo partes procesales:", e)
                return pd.DataFrame()