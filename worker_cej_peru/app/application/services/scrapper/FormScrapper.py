import json
import logging
import os
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from app.domain.interfaces.IGetRecordsService import IGetRecordsService
from app.domain.interfaces.IFormScrapper import IFormScrapper

class FormScrapper(IFormScrapper):
    def __init__(self, getRecords: IGetRecordsService):
        self.getRecords = getRecords    
        self.logger = logging.getLogger(__name__)


    def fill_out_form(self, wait, driver, case_information, actions):
        
        distrito_judicial = case_information.distrito_judicial
        instancia = case_information.instancia
        especialidad = case_information.especialidad
        annio = case_information.annio
        num_expediente = case_information.num_expediente
        radicado = case_information.radicado

        valores_parte = [
            case_information.parte,
            case_information.nombre_completo,
            case_information.demandante,
            case_information.parte_demandante
        ]

        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1.5)

            if radicado:
                self.logger.info("✅ Se encontró el radicado. Filtro por radicado.")
                self.getRecords.get_records_by_Code(driver, wait, radicado)
            else:
                self.logger.info("ℹ️ No hay radicado. Filtro por datos del expediente.")
                self.getRecords.get_records_by_Filters(
                    driver, wait,
                    distrito_judicial, instancia, especialidad, annio, num_expediente
                )

            # 🔁 REINTENTOS CON DIFERENTES VALORES DE PARTE
            for intento, valor_parte in enumerate(valores_parte, start=1):
                if not valor_parte:
                    continue

                self.logger.info(f"🔁 Intento {intento}/4 con PARTE = '{valor_parte}'")

                ok = self._try_parte_with_captcha(
                    wait, driver, actions, valor_parte
                )

                if not ok:
                    continue

                # 🔍 validar si apareció mensaje de error
                if self.is_parte_error(driver):
                    self.logger.warning("⚠️ No hubo resultados, reintentando...")
                    time.sleep(1.2)
                    continue

                # ✅ ÉXITO
                self.logger.info("✅ Expediente encontrado correctamente")
                return True

            # ❌ SI LLEGAMOS AQUÍ → FALLARON LOS 4 INTENTOS
            self.logger.warning("❌ No se encontraron expedientes tras 4 intentos")
            self._save_no_data_case(case_information)
            return False

        except Exception as e:
            self.logger.error(f"⚠️ Error en fill_out_form: {e}", exc_info=True)
            return False

    def _try_parte_with_captcha(self, wait, driver, actions, parte: str) -> bool:
        try:
            # 1️⃣ llenar parte
            parte_inp = wait.until(EC.presence_of_element_located((By.ID, "parte")))
            parte_inp.clear()
            parte_inp.send_keys(parte)
            driver.execute_script(
                "arguments[0].value = arguments[0].value.toUpperCase();",
                parte_inp
            )

            # 2️⃣ generar captcha
            btn_repro = wait.until(EC.element_to_be_clickable((By.ID, "btnRepro")))
            actions.move_to_element(btn_repro).pause(0.2).click(btn_repro).perform()
            time.sleep(1.1)

            hidden = wait.until(EC.presence_of_element_located((By.ID, "1zirobotz0")))
            captcha_val = hidden.get_attribute("value")
            self.logger.info(f"🔐 Captcha obtenido: {captcha_val}")

            # 3️⃣ escribir captcha
            driver.execute_script(
                "document.getElementById('codigoCaptcha').value = arguments[0];",
                captcha_val
            )
            time.sleep(0.4)

            # 4️⃣ consultar
            btn_cons = wait.until(
                EC.element_to_be_clickable((By.ID, "consultarExpedientes"))
            )
            actions.move_to_element(btn_cons).pause(0.2).click(btn_cons).perform()
            self.logger.info("🔎 Consulta enviada")

            time.sleep(1.5)
            return True

        except Exception as e:
            self.logger.warning(f"⚠️ Falló intento con parte '{parte}': {e}")
            return False




    def is_parte_error(self, driver) -> bool:
        try:
            mensaje_no = driver.find_element(By.ID, "mensajeNoExisteExpedientes")
            if mensaje_no.is_displayed():
                self.logger.warning(
                    f"⚠️ Mensaje del sistema: '{mensaje_no.text.strip()}'"
                )
                return True
        except Exception:
            pass
        return False

    
 # ---------------------------------------------------------
    # 📁 GUARDAR EXPEDIENTES SIN RESULTADOS
    # ---------------------------------------------------------
    def _save_no_data_case(self, case_information):

        expediente = {
            "distrito_judicial": case_information.distrito_judicial,
            "instancia": case_information.instancia,
            "especialidad": case_information.especialidad,
            "annio": case_information.annio,
            "num_expediente": case_information.num_expediente,
            "nombre_completo": case_information.nombre_completo,
            "radicado": case_information.radicado,
        }

        json_path = "/app/output/base/expedientes_no_data.json"
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        try:
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            else:
                data = []

            data.append(expediente)

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)

            self.logger.info(f"📁 Expediente guardado en {json_path}")

        except Exception as e:
            self.logger.error(f"❌ Error guardando JSON: {e}", exc_info=True)