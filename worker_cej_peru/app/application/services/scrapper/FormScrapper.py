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

        nombre_completo=case_information.nombre_completo
        
        distrito_judicial = case_information.distrito_judicial
        instancia = case_information.instancia
        especialidad = case_information.especialidad
        annio = case_information.annio
        num_expediente = case_information.num_expediente
        parte = case_information.parte
        radicado = case_information.radicado

        try:
            # 1) esperar que cargue el body
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            # dar un respiro extra
            time.sleep(1.5)

            if radicado:
                self.logger.info("✅ Se encontró el radicado. Se extraerán las actuaciones mediante el filtro por radicado.")
                self.getRecords.get_records_by_Code(driver, wait, radicado)
            else:
                self.logger.info("ℹ️ No se encontró el radicado. Se extraerán las actuaciones mediante la información del caso.")
                self.getRecords.get_records_by_Filters(driver, wait,distrito_judicial,instancia, especialidad,annio,num_expediente)

            parte_inp = wait.until(EC.presence_of_element_located((By.ID, "parte")))
            parte_inp.clear()
            parte_inp.send_keys(parte)
            driver.execute_script("arguments[0].value = arguments[0].value.toUpperCase();", parte_inp)

            # 10) botón audio → crea el hidden
            btn_repro = wait.until(EC.element_to_be_clickable((By.ID, "btnRepro")))
            actions.move_to_element(btn_repro).pause(0.2).click(btn_repro).perform()
            time.sleep(1.1)

            # 11) leer hidden
            hidden = wait.until(EC.presence_of_element_located((By.ID, "1zirobotz0")))
            captcha_val = hidden.get_attribute("value")
            self.logger.info(f"✅ Captcha obtenido: {captcha_val}")

            # 12) escribir captcha rápido
            driver.execute_script(
                "document.getElementById('codigoCaptcha').value = arguments[0];",
                captcha_val
            )
            time.sleep(0.4)

            # 13) consultar
            try:
                btn_cons = driver.find_element(By.ID, "consultarExpedientes")
                actions.move_to_element(btn_cons).pause(0.2).click(btn_cons).perform()
                self.logger.info("🔎 Consulta enviada")
            except Exception as e:
                self.logger.warning(f"⚠️ No pude clicar consultar: {e}")
                return False

            time.sleep(5)

                        # ---------------------------------------------------------
            # 🔍 VERIFICAR SI APARECE EL MENSAJE DE "NO HAY REGISTROS"
                        # ---------------------------------------------------------
            try:
                # Buscar el mensaje del span
                mensaje_no = driver.find_element(By.ID, "mensajeNoExisteExpedientes")

                # Si aparece y está visible, procesamos
                if mensaje_no.is_displayed():
                    texto_mensaje = mensaje_no.text.strip()

                    # Log con el texto exacto del mensaje del sistema
                    self.logger.warning(f"⚠️ Mensaje del sistema: '{texto_mensaje}'")

                    # Guardar screenshot
                    screenshot_path = f"/app/output/img/sinContenido/{num_expediente}_no_hay_expedientes.png"
                    #screenshot_path = f"output/img/sinContenido/{num_expediente}_no_hay_expedientes.png"
                    driver.save_screenshot(screenshot_path)
                    self.logger.info(f"📸 Captura guardada como {screenshot_path}")
                    
                 


                    annio = case_information.annio
                    self.logger.info(f"Año: {annio}")

                    num_expediente = case_information.num_expediente
                    self.logger.info(f"Num Expediente: {num_expediente}")

                    parte = case_information.parte
                    self.logger.info(f"Parte: {parte}")

                    radicado = case_information.radicado

                                        # ------------------------------------------------------
                    # 2) Guardar radicado_update en JSON (APPEND sin sobrescribir)
                    # ------------------------------------------------------
                    expedientes_no_data = {
                        "distrito_judicial": distrito_judicial,
                        "instancia": instancia,
                        "especialidad ": especialidad ,
                        "annio": annio,
                        "num_expediente": num_expediente,
                        "nombre_completo": nombre_completo,
                        
                    }

                    json_path = "/app/output/base/expedientes_no_data.json"
                    #json_path = "output/base/expedientes_no_data.json"
                    # Crear carpeta si no existe
                    os.makedirs(os.path.dirname(json_path), exist_ok=True)

                    # Si el JSON NO existe → crearlo con una lista inicial
                    if not os.path.exists(json_path):
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump([expedientes_no_data], f, indent=4, ensure_ascii=False)
                    else:
                        # Si ya existe, cargar y agregar
                        try:
                            with open(json_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                        except Exception:
                            data = []   # si está corrupto o vacío, iniciar lista nueva

                        data.append(expedientes_no_data)

                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4, ensure_ascii=False)

                    return False

            except Exception as e:
                # El span no existe → seguir el flujo normal
                self.logger.debug(f"ℹ️ No apareció mensaje de 'no existen expedientes': {e}")
                pass

             # Screenshot
         

            
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(1.5)

            # # Esperar a que aparezca el div con la clase del resultado
            # radicado = None
            # cod_despacho_rama = None

            # try:
            #     # Esperar hasta que aparezca el número de expediente
            #     radicado_element = wait.until(
            #         EC.visibility_of_element_located((By.CSS_SELECTOR, "div.divNroJuz b"))
            #     )
            #     # Obtener todos los <b> dentro de la clase divNroJuz
            #     elementos_b = driver.find_elements(By.CSS_SELECTOR, "div.divNroJuz b")

            #     # El primero es el radicado, el segundo el juzgado
            #     if not radicado:
            #         radicado = elementos_b[0].text.strip()
            #         self.logger.info(f"🔎 Radicado encontrado: {radicado}")
                    
            #     cod_despacho_rama = elementos_b[1].text.strip()
            #     self.logger.info(f"🏛️ Despacho o rama: {cod_despacho_rama}")

            #     if not radicado:
            #         self.logger.info(f" No se encontro radicado ")


            #     self.getRecords.get_actors(wait, radicado)

            # except Exception as e:
            #     self.logger.warning(f"⚠️ No se encontró el elemento del radicado: {e}")
            #     return None, None



            # if radicado:
            #     # ------------------------------------------------------
            #     # 1) Guardar screenshot
            #     # ------------------------------------------------------
            #     screenshot_path = f"/app/output/img/{radicado}_{num_expediente}.png"
            #     driver.save_screenshot(screenshot_path)
            #     self.logger.info(f"📸 Captura guardada como {radicado}_{num_expediente}.png")

            #     # ------------------------------------------------------
            #     # 2) Guardar radicado_update en JSON (APPEND sin sobrescribir)
            #     # ------------------------------------------------------
            #     radicado_update = {
            #         "radicado": radicado,
            #         "num_exp": num_expediente,
            #         "nombre_completo":nombre_completo,
            #         "annio": annio
            #     }

            #     json_path = "/app/output/base/radicados_update.json"

            #     # Crear carpeta si no existe
            #     os.makedirs(os.path.dirname(json_path), exist_ok=True)

            #     # Si el JSON NO existe → crearlo con una lista inicial
            #     if not os.path.exists(json_path):
            #         with open(json_path, "w", encoding="utf-8") as f:
            #             json.dump([radicado_update], f, indent=4, ensure_ascii=False)
            #     else:
            #         # Si ya existe, cargar y agregar
            #         try:
            #             with open(json_path, "r", encoding="utf-8") as f:
            #                 data = json.load(f)
            #         except Exception:
            #             data = []   # si está corrupto o vacío, iniciar lista nueva

            #         data.append(radicado_update)

            #         with open(json_path, "w", encoding="utf-8") as f:
            #             json.dump(data, f, indent=4, ensure_ascii=False)




            # try:
            #     form = WebDriverWait(driver, 10).until(
            #         EC.presence_of_element_located((By.CSS_SELECTOR, "form[id='command']"))
            #     )
            #     button = form.find_element(By.TAG_NAME, "button")
            #     actions.move_to_element(button).pause(0.2).click(button).perform()
            #     self.logger.info("✅ Botón del expediente clicado correctamente.")
            # except Exception as e:
            #     self.logger.warning(f"⚠️ No pude clicar el botón del expediente: {e}")
            #     return None, None

            # wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            # time.sleep(1.5)


            return True

        except Exception as e:
            self.logger.error(f"⚠️ Error en fill_out_form: {e}", exc_info=True)
            return False
