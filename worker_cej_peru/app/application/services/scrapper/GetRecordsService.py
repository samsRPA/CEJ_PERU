import json
import os
import time
import re
import logging
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from app.domain.interfaces.IGetRecordsService import IGetRecordsService

class GetRecordsService(IGetRecordsService):

    
    def __init__(self):
        self.logger=logging.getLogger(__name__)
        
    def _wait_select_has_at_least(self,driver, select_locator, min_options, timeout=15):
        """espera hasta que el select tenga X opciones reales"""
        end = time.time() + timeout
        while time.time() < end:
            try:
                sel = driver.find_element(*select_locator)
                opts = sel.find_elements(By.TAG_NAME, "option")
                if len(opts) >= min_options:
                    return sel
            except Exception:
                pass
            time.sleep(0.4)
        raise TimeoutException(f"el select {select_locator} no llegó a {min_options} opciones")


    def get_records_by_Code(self,driver, wait, radicado):
        try:
            # Esperar a que el tab esté visible y hacer clic
            tab_codigo = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Por Código de Expediente')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", tab_codigo)
            time.sleep(0.5)
            tab_codigo.click()
            self.logger.info("🟢 Se hizo clic en la pestaña 'Por Código de Expediente'")

            # --- Dividir el radicado ---
            partes = radicado.split("-")
            if len(partes) != 7:
                self.logger.warning("⚠️ Formato de radicado inesperado:", radicado)
                return
            self.logger.info(f"📦 Partes del radicado: {partes}")

                    # --- IDs de los inputs según el orden ---
            input_ids = [
                "cod_expediente",
                "cod_anio",
                "cod_incidente",
                "cod_distprov",
                "cod_organo",
                "cod_especialidad",
                "cod_instancia"
            ]

            # --- Llenar dinámicamente cada campo ---
            for i, input_id in enumerate(input_ids):
                try:
                    elemento = wait.until(EC.visibility_of_element_located((By.ID, input_id)))
                    driver.execute_script("arguments[0].scrollIntoView(true);", elemento)
                    time.sleep(0.2)
                    driver.execute_script("arguments[0].focus();", elemento)
                    elemento.clear()
                    elemento.send_keys(partes[i])
                    self.logger.info(f"✅ Campo '{input_id}' llenado con: {partes[i]}")
                except Exception as e:
                    self.logger.warning(f"⚠️ No se pudo llenar el campo '{input_id}': {e}")


        except Exception as e:
            self.logger.warning("⚠️ Error al manejar la pestaña 'Por Código de Expediente':", e)

    def get_records_by_Filters(self, driver, wait, distrito_judicial, instancia, especialidad, annio, num_expediente):
        try:
            # 2) esperar a que el select de distrito tenga TODAS las opciones (al menos 20)
            sel_distr = self._wait_select_has_at_least(
                driver,
                (By.ID, "distritoJudicial"),
                min_options=20,
                timeout=20
            )

            total_distr = len(sel_distr.find_elements(By.TAG_NAME, "option"))
            self.logger.info(f"✅ distritoJudicial cargó con {total_distr} opciones")

            # --- Seleccionar distrito judicial ---
            try:
                options = sel_distr.find_elements(By.TAG_NAME, "option")
                ok = False
                for o in options:
                    if o.text.strip().upper() == distrito_judicial:
                        Select(sel_distr).select_by_visible_text(o.text)
                        ok = True
                        self.logger.info(f"✅ Distrito {distrito_judicial} seleccionado por texto")
                        break

                if not ok:
                    self.logger.error(f"❌ No pude seleccionar {distrito_judicial}, opciones reales:")
                    for o in options:
                        self.logger.info(f"  - {o.get_attribute('value')} | {o.text}")
                    return

            except Exception:
                self.logger.error("❌ Error al seleccionar el distrito judicial")
                return

            # --- Instancia ---
            try:
                sel_inst = wait.until(EC.presence_of_element_located((By.ID, "organoJurisdiccional")))

                # Esperar que carguen opciones
                end = time.time() + 15
                while time.time() < end:
                    opts = sel_inst.find_elements(By.TAG_NAME, "option")
                    if len(opts) > 1:
                        break
                    time.sleep(0.4)

                inst_opts = sel_inst.find_elements(By.TAG_NAME, "option")
                self.logger.info("📋 Opciones de instancia que llegaron:")
                for o in inst_opts:
                    self.logger.info(f"   - {o.get_attribute('value')} | {o.text}")

                picked_inst = False
                for o in inst_opts:
                    if o.text.strip().upper() == instancia:
                        Select(sel_inst).select_by_visible_text(o.text)
                        picked_inst = True
                        self.logger.info(f"✅ Instancia seleccionada: {o.text}")
                        break

                if not picked_inst:
                    self.logger.warning(f"❌ Instancia '{instancia}' no encontrada en las opciones")
                    return

                time.sleep(0.6)

            except Exception:
                self.logger.error("❌ Error al seleccionar la instancia")
                return

            # --- Especialidad ---
            try:
                sel_esp = wait.until(EC.presence_of_element_located((By.ID, "especialidad")))

                end = time.time() + 10
                while time.time() < end:
                    esp_opts = sel_esp.find_elements(By.TAG_NAME, "option")
                    if len(esp_opts) > 1:
                        break
                    time.sleep(0.4)

                options = sel_esp.find_elements(By.TAG_NAME, "option")
                ok = False
                for o in options:
                    if o.text.strip().upper() == especialidad:
                        Select(sel_esp).select_by_visible_text(o.text)
                        ok = True
                        self.logger.info(f"✅ Especialidad {especialidad} seleccionada por texto")
                        break

                if not ok:
                    self.logger.error(f"❌ No pude seleccionar {especialidad}, opciones reales:")
                    for o in options:
                        self.logger.info(f"  - {o.get_attribute('value')} | {o.text}")
                    return

            except Exception:
                self.logger.error("❌ Error al seleccionar la especialidad")
                return

            # --- Año ---
            try:
                sel_anio = wait.until(EC.presence_of_element_located((By.ID, "anio")))
                Select(sel_anio).select_by_value(annio)
                self.logger.info(f"✅ Año {annio} seleccionado")

            except Exception:
                self.logger.error("❌ Error al seleccionar el año")
                return

            # --- Número de Expediente ---
            try:
                num_inp = wait.until(EC.presence_of_element_located((By.ID, "numeroExpediente")))
                num_inp.clear()
                num_inp.send_keys(num_expediente)
                self.logger.info(f"📄 Número de expediente ingresado: {num_expediente}")

            except Exception:
                self.logger.error("❌ Error al ingresar el número de expediente")
                return

           

        except Exception as e:
            self.logger.error(f"⚠️ ERROR en get_records_by_Filters: {e}")

    # def get_actors(self,wait, radicado):
    #     try:
    #         # Esperar el elemento con las partes
    #         parte_element = wait.until(
    #             EC.visibility_of_element_located((By.CSS_SELECTOR, "div.partesp"))
    #         )
    #         texto = parte_element.text.strip()

    #         # Extraer los bloques de texto (DEMANDANTE / DEMANDADO)
    #         patrones = re.findall(r"(DEMANDANTE|DEMANDADO):\s*([^:]+?)(?=(?:DEMANDANTE|DEMANDADO|$))", texto)

    #         # Convertir a DataFrame directamente
    #         df = pd.DataFrame(patrones, columns=["TIPO_SUJETO", "NOMBRE_ACTOR"])

    #         # Limpiar texto y separar demandados múltiples por coma
    #         df["NOMBRE_ACTOR"] = df["NOMBRE_ACTOR"].str.replace(r"\.$", "", regex=True)
    #         df = df.assign(NOMBRE_ACTOR=df["NOMBRE_ACTOR"].str.split(","))

    #         # Expandir los nombres separados por coma (sin usar for)
    #         df = df.explode("NOMBRE_ACTOR").reset_index(drop=True)
    #         df["NOMBRE_ACTOR"] = df["NOMBRE_ACTOR"].str.strip()

    #         # Reemplazar DEMANDANTE por ACTOR
    #         df["TIPO_SUJETO"] = df["TIPO_SUJETO"].replace({"DEMANDANTE": "ACTOR"})

    #         # Agregar columnas fijas
    #         df["RADICADO_RAMA"] = radicado
    #         df["ORIGEN_DATOS"] = "CEJ_PERU"

    #         # Reordenar columnas
    #         df = df[["RADICADO_RAMA", "TIPO_SUJETO", "NOMBRE_ACTOR", "ORIGEN_DATOS"]]

    #         output_path = "/app/output/jsons/sujetos.json"

    #         # Convertir el DataFrame a lista de diccionarios
    #         new_data = df.to_dict(orient="records")

    #         # Si el archivo existe, cargar su contenido
    #         if os.path.exists(output_path):
    #             with open(output_path, "r", encoding="utf-8") as f:
    #                 try:
    #                     existing_data = json.load(f)
    #                 except json.JSONDecodeError:
    #                     existing_data = []  # En caso de JSON corrupto o vacío
    #         else:
    #             existing_data = []

    #         # Agregar los nuevos datos al JSON existente (sin duplicar si es necesario)
    #         existing_data.extend(new_data)

    #         # Guardar el JSON actualizado
    #         with open(output_path, "w", encoding="utf-8") as f:
    #             json.dump(existing_data, f, ensure_ascii=False, indent=4)

    #         print("✅ Datos agregados correctamente en sujetos.json")

    #         return df

    #     except TimeoutException:
    #         print("⚠️ No se encontró el elemento de partes procesales.")
    #         return pd.DataFrame()
    #     except Exception as e:
    #         print("❌ Error extrayendo partes procesales:", e)
    #         return pd.DataFrame()
        


