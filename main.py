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

import requests

import re
import json
import pandas as pd


CHROME_MAJOR = 141
URL = "https://cej.pj.gob.pe/cej/forms/busquedaform.html"

# datos que quieres
DISTRITO_VALUE = "20305"                  # CALLAO
INSTANCIA_TEXT = "JUZGADO DE PAZ LETRADO"
ESPECIALIDAD_VALUE = "32047"              # CIVIL
ANIO_VALUE = "2016"
NUM_EXPEDIENTE = "1889"
PARTE_TEXT = "GOIN RODRIGUEZ"




CHROME_MAJOR = 141
DOWNLOAD_DIR ="/app/output/descargas"

def crear_driver():
    # Crear carpeta de descargas si no existe
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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
        "download.default_directory": DOWNLOAD_DIR,              # Ruta donde guardar
        "download.prompt_for_download": False,                   # No preguntar dónde guardar
        "download.directory_upgrade": True,                      # Permitir sobrescribir
        "safebrowsing.enabled": True,                            # Permitir descargas sin alerta
        "profile.default_content_settings.popups": 0,            # Bloquear popups
    }
    opts.add_experimental_option("prefs", prefs)

    # Crear el driver
    driver = uc.Chrome(options=opts, version_main=CHROME_MAJOR)

    # Ocultar bandera "webdriver"
    try:
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    except Exception:
        pass

    return driver


def wait_select_has_at_least(driver, select_locator, min_options, timeout=15):
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


def click_por_codigo_expediente(driver, wait, radicado):
    try:
        # Esperar a que el tab esté visible y hacer clic
        tab_codigo = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Por Código de Expediente')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", tab_codigo)
        time.sleep(0.5)
        tab_codigo.click()
        print("🟢 Se hizo clic en la pestaña 'Por Código de Expediente'")

        # --- Dividir el radicado ---
        partes = radicado.split("-")
        if len(partes) != 7:
            print("⚠️ Formato de radicado inesperado:", radicado)
            return
        print(f"📦 Partes del radicado: {partes}")

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
                print(f"✅ Campo '{input_id}' llenado con: {partes[i]}")
            except Exception as e:
                print(f"⚠️ No se pudo llenar el campo '{input_id}': {e}")


    except Exception as e:
        print("⚠️ Error al manejar la pestaña 'Por Código de Expediente':", e)


def click_por_filtros(driver, wait):
    try:
       # 2) esperar a que el select de distrito tenga TODAS las opciones (al menos 20)
            sel_distr = wait_select_has_at_least(
                driver,
                (By.ID, "distritoJudicial"),
                min_options=20,   # las que tú viste en el HTML
                timeout=20
            )
            print("✅ distritoJudicial cargó con", len(sel_distr.find_elements(By.TAG_NAME, "option")), "opciones")

            # 3) seleccionar CALLAO por value (si no está, lo haremos por texto)
            try:
                Select(sel_distr).select_by_value(DISTRITO_VALUE)
                print("✅ Distrito CALLAO seleccionado por value")
            except Exception:
                # fallback por texto
                options = sel_distr.find_elements(By.TAG_NAME, "option")
                ok = False
                for o in options:
                    if o.text.strip().upper() == "CALLAO":
                        Select(sel_distr).select_by_visible_text(o.text)
                        ok = True
                        print("✅ Distrito CALLAO seleccionado por texto")
                        break
                if not ok:
                    print("❌ No pude seleccionar CALLAO, opciones reales:")
                    for o in options:
                        print("  -", o.get_attribute("value"), "|", o.text)
                    return

            # 4) ahora SÍ hay que esperar a que se cargue la instancia
            # primero obtenemos el select
            sel_inst = wait.until(EC.presence_of_element_located((By.ID, "organoJurisdiccional")))
            # y ahora esperamos a que tenga más de 1 opción (que ya no sea solo --Seleccionar)
            end = time.time() + 15
            while time.time() < end:
                opts = sel_inst.find_elements(By.TAG_NAME, "option")
                # si ya hay varias, rompemos
                if len(opts) > 1:
                    break
                time.sleep(0.4)

            # imprimir lo que realmente llegó
            inst_opts = sel_inst.find_elements(By.TAG_NAME, "option")
            print("📋 Opciones de instancia que llegaron:")
            for o in inst_opts:
                print("   -", o.get_attribute("value"), "|", o.text)

            # 5) intentar seleccionar por texto
            picked_inst = False
            for o in inst_opts:
                if o.text.strip().upper() == INSTANCIA_TEXT:
                    Select(sel_inst).select_by_visible_text(o.text)
                    picked_inst = True
                    print("✅ Instancia seleccionada:", o.text)
                    break

            if not picked_inst:
                # fallback: tomar la primera opción real
                if len(inst_opts) > 1:
                    Select(sel_inst).select_by_index(1)
                    print("⚠️ No estaba la instancia pedida, tomé la primera disponible:", inst_opts[1].text)
                else:
                    print("❌ No había instancia disponible, no se puede seguir.")
                    return

            time.sleep(0.6)

            # 6) especialidad (también dependiente)
            sel_esp = wait.until(EC.presence_of_element_located((By.ID, "especialidad")))
            # esperar a que tenga al menos 2 opciones
            end = time.time() + 10
            while time.time() < end:
                esp_opts = sel_esp.find_elements(By.TAG_NAME, "option")
                if len(esp_opts) > 1:
                    break
                time.sleep(0.4)

            # intentar seleccionar CIVIL por value
            try:
                Select(sel_esp).select_by_value(ESPECIALIDAD_VALUE)
                print("✅ Especialidad CIVIL seleccionada")
            except Exception:
                # fallback: mostrar lo que hay
                print("⚠️ No encontré la especialidad por value, estas son las opciones:")
                for o in sel_esp.find_elements(By.TAG_NAME, "option"):
                    print("   -", o.get_attribute("value"), "|", o.text)
                # tomar la primera real si existe
                if len(esp_opts) > 1:
                    Select(sel_esp).select_by_index(1)
                    print("⚠️ Tomé la primera especialidad disponible")
                else:
                    return

            # 7) año
            sel_anio = wait.until(EC.presence_of_element_located((By.ID, "anio")))
            Select(sel_anio).select_by_value(ANIO_VALUE)
            print("✅ Año", ANIO_VALUE, "seleccionado")

            # 8) número expediente
            num_inp = wait.until(EC.presence_of_element_located((By.ID, "numeroExpediente")))
            num_inp.clear()
            num_inp.send_keys(NUM_EXPEDIENTE)
    except Exception as e:
        print("ERROR:", e)



def extraer_sujetos(wait, radicado):
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

        # Guardar como JSON
        df.to_json("/app/output/sujetos.json", orient="records", indent=4, force_ascii=False)

        print("✅ Datos extraídos y guardados en sujetos.json")
        return df

    except TimeoutException:
        print("⚠️ No se encontró el elemento de partes procesales.")
        return pd.DataFrame()
    except Exception as e:
        print("❌ Error extrayendo partes procesales:", e)
        return pd.DataFrame()



# def extraer_todos_los_pnl(driver, radicado,cod_despacho_rama):
#     resoluciones = []
#         # 👇 Fuerza a que todos los paneles sean visibles
#     driver.execute_script("""
#         document.querySelectorAll("div[id^='pnlSeguimiento']").forEach(e => e.style.display = 'block');
#     """)
#     bloques = driver.find_elements(By.CSS_SELECTOR, "div[id^='pnlSeguimiento']")
#     print(f"📄 Se encontraron {len(bloques)} paneles de seguimiento.")

#     os.makedirs(DOWNLOAD_DIR, exist_ok=True)

#     for idx, bloque in enumerate(bloques, start=1):
#         print(f"\n🔹 Procesando panel {idx}...")
#         data = {"panel": idx}

#         # --- Función segura para obtener texto ---
#         def safe_text(xpath):
#             try:
#                 return bloque.find_element(By.XPATH, xpath).text.strip()
#             except:
#                 return None
#         fecha_res=None
#         # --- Verificar si hay mensaje de no visualización ---
#         downloadable=None
#         try:
#             msg = bloque.find_element(By.CSS_SELECTOR, "div.sinResol.divResolPar").text.strip()
#             if "Los escritos no se pueden visualizar" in msg:
#                 print("⚠️ Los escritos no se pueden visualizar por este medio.")
#                 fecha_res = safe_text(".//div[div[contains(.,'Fecha de Ingreso:')]]/div[@class='fleft']")
#                 downloadable = False
#             else:
#                 fecha_res = safe_text(".//div[div[contains(.,'Fecha de Resolución:')]]/div[@class='fleft']")
#                 downloadable = True
#         except NoSuchElementException:
#             # Si no hay div.sinResol.divResolPar, asumimos que sí tiene resolución
#             fecha_res = safe_text(".//div[div[contains(.,'Fecha de Resolución:')]]/div[@class='fleft']")
#             downloadable = True


      
#         # --- Convertir formato de fecha: 30/10/2018 → 30-10-2018 ---
#         if fecha_res:
#             try:
#                 fecha_obj = datetime.strptime(fecha_res.strip(), "%d/%m/%Y")
#                 fecha_formateada = fecha_obj.strftime("%d-%m-%Y")
#             except ValueError:
#                     fecha_formateada = fecha_res.strip() if fecha_res else None
#         else:
#             fecha_formateada = None
            


#         data["radicado"] = radicado
#         data["cod_despacho_rama"] = cod_despacho_rama
#         data["fecha"]=fecha_formateada
#         data["actuacion_rama"] = safe_text(".//div[contains(.,'Acto:')]/following-sibling::div[contains(@class,'fleft')]")
#         data["anotacion_rama"]=safe_text(".//div[div[contains(.,'Sumilla:')]]/div[@class='fleft']")
#         data["origen_datos"]="CEJ_PERU"
#         data["fecha_registro_tyba"]=fecha_formateada
#         #data["Tipo de Notificación"] = safe_text(".//div[div[contains(.,'Tipo de Notificación:')]]/div[@class='fleft']")
#         #data["Acto"] = safe_text(".//div[div[contains(.,'Acto:')]]/div[@class='fleft']")
#         #data["Fojas"] = safe_text(".//div[div[contains(.,'Fojas:')]]/div[@class='fleft']")
#         #data["Proveido"] = safe_text(".//div[div[contains(.,'Proveido:')]]/div[@class='fleft']")
#         #data["Sumilla"] = safe_text(".//div[div[contains(.,'Sumilla:')]]/div[@class='fleft']")
#         #data["Descripción de Usuario"] = safe_text(".//div[div[contains(.,'Descripción de Usuario:')]]/div[@class='fleft']")

        
#         if downloadable:
   
#             # --- Intentar hacer clic en el botón de descarga ---
#             try:
#                 boton = bloque.find_element(By.CSS_SELECTOR, "a.aDescarg")
#                 driver.execute_script("arguments[0].scrollIntoView(true);", boton)
#                 time.sleep(0.5)
#                 try:
#                     boton.click()
#                 except ElementClickInterceptedException:
#                     driver.execute_script("arguments[0].click();", boton)

#                 print("📥 Click en botón de descarga realizado.")

#                 # --- Esperar a que se complete la descarga ---
#                 archivo_descargado = None
#                 timeout = 30  # segundos
#                 for _ in range(timeout):
#                     archivos = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".pdf")]
#                     parciales = [f for f in os.listdir(DOWNLOAD_DIR) if f.endswith(".crdownload")]

#                     if archivos and not parciales:
#                         archivo_descargado = max(
#                             [os.path.join(DOWNLOAD_DIR, f) for f in archivos],
#                             key=os.path.getmtime  # el más reciente
#                         )
#                         break
#                     time.sleep(1)

#                 if not archivo_descargado:
#                     print("❌ No se detectó archivo descargado.")
#                     continue

#                 # --- Renombrar el archivo ---
#                 if fecha_res:
#                     try:
#                         fecha_str = datetime.strptime(fecha_res, "%d/%m/%Y").strftime("%d-%m-%Y")
#                     except ValueError:
#                         fecha_str = datetime.now().strftime("%d-%m-%Y")
#                 else:
#                     fecha_str = datetime.now().strftime("%d-%m-%Y")

#                 nuevo_nombre = f"{fecha_str}_{radicado}.pdf"
#                 destino = os.path.join(DOWNLOAD_DIR, nuevo_nombre)

#                 # Evitar reemplazo accidental
#                 if os.path.exists(destino):
#                     base, ext = os.path.splitext(destino)
#                     destino = f"{base}_{int(time.time())}{ext}"

#                 os.rename(archivo_descargado, destino)
#                 nuevo_nombre = os.path.basename(destino)

#                 print(f"✅ Archivo renombrado a: {nuevo_nombre}")
#                 #data["Archivo"] = nuevo_nombre
                

#             except NoSuchElementException:
#                 print("⚠️ No se encontró enlace de descarga en este panel.")
#                 continue
#             except ElementNotInteractableException:
#                 print("❌ Error: botón no interactuable.")
#                 continue
#             except Exception as e:
#                 print(f"❌ Error al intentar descargar: {e}")
#                 continue

#         resoluciones.append(data)

#     # --- Guardar datos en JSON ---
#     json_path = os.path.join("/app/output/", f"resoluciones-{radicado}.json")
#     with open(json_path, "w", encoding="utf-8") as f:
#         json.dump(resoluciones, f, indent=4, ensure_ascii=False)

#     print(f"\n✅ Se guardaron {len(resoluciones)} paneles con descarga disponible.")
#     print(f"📁 JSON guardado en: {json_path}")
#     return resoluciones



def extraer_todos_los_pnl(driver, radicado, cod_despacho_rama):
    resoluciones = []
    consecutivos = defaultdict(int)  # 🔢 Lleva el conteo de consecutivos por (radicado, fecha)

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
        print(f"📄 Se encontraron {len(bloques)} paneles de seguimiento visibles.")
    except Exception as e:
        print(f"⚠️ Advertencia: no se pudieron cargar todos los paneles a tiempo → {e}")

       
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    consecutivo=0
    for idx, bloque in enumerate(bloques, start=1):
        print(f"\n🔹 Procesando panel {idx}...")
        data = {"panel": idx}

        # --- Función segura para obtener texto ---
        def safe_text(xpath):
            try:
                return bloque.find_element(By.XPATH, xpath).text.strip()
            except:
                return None

        fecha_res = None
        downloadable = None

        # --- Verificar si hay mensaje de no visualización ---
       # --- Verificar si hay mensaje de no visualización ---
        try:
            msg = bloque.find_element(By.CSS_SELECTOR, "div.sinResol.divResolPar").text.strip()
            if "Los escritos no se pueden visualizar" in msg:
                print("⚠️ Los escritos no se pueden visualizar por este medio.")
                # 🔹 En estos casos, la fecha está en "Fecha de Ingreso"
                fecha_res = safe_text(".//div[div[contains(.,'Fecha de Ingreso:')]]/div[@class='fleft']")
                downloadable = False
            else:
                # 🔹 Si hay documento, tomamos "Fecha de Resolución"
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
                print(f"⚠️ No se pudo parsear la fecha: {fecha_res}")

        # --- Datos base del registro ---
        data["radicado"] = radicado
        data["cod_despacho_rama"] = cod_despacho_rama
        data["fecha"] = fecha_formateada
        data["actuacion_rama"] = safe_text(".//div[contains(.,'Acto:')]/following-sibling::div[contains(@class,'fleft')]")
        data["anotacion_rama"] = safe_text(".//div[div[contains(.,'Sumilla:')]]/div[@class='fleft']")
        data["origen_datos"] = "CEJ_PERU"
        data["fecha_registro_tyba"] = fecha_registro_tyba
        
        if downloadable:
            try:
                enlace = bloque.find_element(By.CSS_SELECTOR, "a.aDescarg")

                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'center'});", enlace)
                time.sleep(0.3)

                try:
                    enlace.click()
                    print("📥 Documento descargado con click normal.")
                except:
                    print("⚠️ Click interceptado, aplicando click por JavaScript...")
                    driver.execute_script("arguments[0].click();", enlace)
                    print("✅ Documento descargado con click JS.")

                # Esperar descarga
                time.sleep(2)

                # ✅ Detectar archivo descargado más reciente (.crdownload o .pdf)
                lista = glob.glob(os.path.join(DOWNLOAD_DIR, "*"))
                if not lista:
                    print("⚠️ No hay archivos en la carpeta de descarga.")
                else:
                    archivo_reciente = max(lista, key=os.path.getctime)

                    # Esperar a que termine si está en progreso (.crdownload)
                    while archivo_reciente.endswith(".crdownload"):
                        time.sleep(0.5)
                        lista = glob.glob(os.path.join(DOWNLOAD_DIR, "*"))
                        archivo_reciente = max(lista, key=os.path.getctime)
                    consecutivo += 1
                    nuevo_nombre = f"{fecha_formateada}_{radicado}_{consecutivo}.pdf"
                    nuevo_path = os.path.join(DOWNLOAD_DIR, nuevo_nombre)

                    os.rename(archivo_reciente, nuevo_path)
                    print(f"✅ Archivo renombrado como: {nuevo_nombre}")
                    data["descargado"] = True
                    data["consecutivo"]=consecutivo

            except NoSuchElementException:
                print("ℹ️ No hay enlace de descarga en este panel.")
                data["descargado"] = False
            except Exception as e:
                print(f"❌ Error al intentar descargar: {e}")
                data["descargado"] = False

        resoluciones.append(data)
    # --- Guardar datos en JSON ---
    json_path = os.path.join("/app/output/", f"resoluciones-{radicado}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(resoluciones, f, indent=4, ensure_ascii=False)

 
    print(f"📁 JSON guardado en: {json_path}")
    return resoluciones




def main(radicado):
    driver = None
    try:
        driver = crear_driver()
        driver.get(URL)
        wait = WebDriverWait(driver, 20)
        actions = ActionChains(driver)

        # 1) esperar que cargue el body
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        # dar un respiro extra
        time.sleep(1.5)


        if radicado:
            click_por_codigo_expediente(driver, wait,radicado)
        else:
            click_por_filtros(driver, wait)

     

            # 9) parte
        parte_inp = wait.until(EC.presence_of_element_located((By.ID, "parte")))
        parte_inp.clear()
        parte_inp.send_keys(PARTE_TEXT)
        driver.execute_script("arguments[0].value = arguments[0].value.toUpperCase();", parte_inp)

            # 10) botón audio → crea el hidden
        btn_repro = wait.until(EC.element_to_be_clickable((By.ID, "btnRepro")))
        actions.move_to_element(btn_repro).pause(0.2).click(btn_repro).perform()
        time.sleep(1.1)

            # 11) leer hidden
        hidden = wait.until(EC.presence_of_element_located((By.ID, "1zirobotz0")))
        captcha_val = hidden.get_attribute("value")
        print("✅ Captcha obtenido:", captcha_val)

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
            print("🔎 Consulta enviada")
        except Exception as e:
            print("⚠️ No pude clicar consultar:", e)

        
            # Esperar a que aparezca el div con la clase del resultado
        radicado = None
        cod_despacho_rama = None

        try:
                # Esperar hasta que aparezca el número de expediente
            radicado_element = wait.until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div.divNroJuz b"))
            )
                # Obtener todos los <b> dentro de la clase divNroJuz
            elementos_b = driver.find_elements(By.CSS_SELECTOR, "div.divNroJuz b")

                # El primero es el radicado, el segundo el juzgado
            radicado = elementos_b[0].text.strip()
            cod_despacho_rama = elementos_b[1].text.strip()

            print(f"🔎 Radicado encontrado: {radicado}")
            print(f"🏛️ Despacho o rama: {cod_despacho_rama}")

            if radicado:
                radicado = radicado.replace("-", "")
                extraer_sujetos(wait, radicado)

        except Exception as e:
            print("⚠️ No se encontró el elemento del radicado:", e)

      
        try:
            form = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form[id='command']"))
            )
            button = form.find_element(By.TAG_NAME, "button")

            actions.move_to_element(button).pause(0.2).click(button).perform()
            print("✅ Botón del expediente clicado correctamente.")

        except Exception as e:
            print("⚠️ No pude clicar el botón del expediente:", e)


            
        time.sleep(4)
        driver.save_screenshot("/app/output/cej_result3.png")

        
        print("📸 Screenshot guardado: cej_result3.png")

        if radicado and cod_despacho_rama:
           
            extraer_todos_los_pnl(driver, radicado, cod_despacho_rama)
        else:
            print("⚠️ No se pudo extraer radicado o despacho, se omite procesamiento.")

    except Exception as e:
        print("ERROR:", e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                try:
                    driver.service.stop()
                except Exception:
                    pass

if __name__ == "__main__":
    radicado="01889-2016-0-0701-JP-CI-01"
    #radicado=None
    main(radicado)
