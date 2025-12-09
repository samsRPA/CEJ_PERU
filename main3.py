import json
import pandas as pd
import os
import logging

def update_radicados():
    try:
        json_path = "output/base/radicados_update.json"
        excel_path = "output/base/OBLIGACIONES_ACTUALIZADO Y REVISADO MANUAL.xlsx"

        # 1) Cargar JSON
        if not os.path.exists(json_path):
            logging.error("❌ No existe radicados_update.json")
            return
        
        with open(json_path, "r", encoding="utf-8") as f:
            radicados_data = json.load(f)

        if not isinstance(radicados_data, list):
            logging.error("❌ El JSON no es una lista")
            return

        # 2) Cargar Excel
        df = pd.read_excel(excel_path)
        df.columns = df.columns.str.strip().str.upper()

        # --- Normalizar columnas necesarias ---
        required_cols = ["NOMBRE CLIENTE", "EXP JUDICIAL", "AÑO"]
        for col in required_cols:
            if col not in df.columns:
                logging.error(f"❌ Falta la columna '{col}' en el Excel")
                return

        # Crear columna RADICADO LARGO si no existe
        if "RADICADO LARGO" not in df.columns:
            logging.warning("⚠️ No existe 'RADICADO LARGO', creando columna vacía.")
            df["RADICADO LARGO"] = ""

        df["RADICADO LARGO"] = df["RADICADO LARGO"].astype("object")

        # 3) Procesar JSON
        for item in radicados_data:
            radicado = str(item.get("radicado", "")).strip()
            num_exp = str(item.get("num_exp", "")).strip()
            nombre = str(item.get("nombre_completo", "")).strip().upper()
            annio = str(item.get("annio", "")).strip()

            if not radicado or not num_exp or not nombre or not annio:
                logging.warning(f"⚠️ Registro inválido en JSON: {item}")
                continue

            # --- Buscar coincidencia por 3 columnas ---
            mask = (
                df["NOMBRE CLIENTE"].astype(str).str.strip().str.upper() == nombre
            ) & (
                df["EXP JUDICIAL"].astype(str).str.strip() == num_exp
            ) & (
                df["AÑO"].astype(str).str.strip() == annio
            )

            if mask.sum() == 0:
                logging.warning(f"⚠️ No se encontró coincidencia exacta para: {item}")
                continue

            # 🔥 Obtener radicados previos
            prev_value = df.loc[mask, "RADICADO LARGO"].astype(str).tolist()

            # Convertir lista de valores previos en set de radicados
            radicados_previos = set()
            for val in prev_value:
                if val.strip():
                    for r in val.split(","):
                        r = r.strip()
                        if r:
                            radicados_previos.add(r)

            # ➕ Agregar el nuevo radicado al set
            radicados_previos.add(radicado)

            # Ordenar para que quede bonito
            new_value = ", ".join(sorted(radicados_previos))

            # Guardar
            df.loc[mask, "RADICADO LARGO"] = new_value

            logging.info(f"📝 Agregado radicado: {nombre} | {num_exp}-{annio} → {new_value}")

        # 4) Guardar Excel actualizado
        df.to_excel(excel_path, index=False)
        logging.info("💾 Excel BASE PERU actualizado correctamente usando el JSON (multiradicado).")

    except Exception as e:
        logging.error(f"❌ Error procesando radicados_update.json: {e}")


def update_actuaciones():
    excel_path = "output/base/OBLIGACIONES_ACTUALIZADO Y REVISADO MANUAL.xlsx"
    json_path = "output/jsons/actuaciones.json"

    # --- Cargar Excel ---
    df = pd.read_excel(excel_path)
    df["RADICADO LARGO"] = df["RADICADO LARGO"].astype(str).str.strip()

    # Crear columna ACTUACION si no existe
    if "ACTUACION" not in df.columns:
        df["ACTUACION"] = ""

    # --- Cargar JSON ---
    with open(json_path, "r", encoding="utf-8") as f:
        actuaciones_json = json.load(f)

    # Crear índice → guardar el JSON COMPLETO sin tocarlo
    index_por_radicado = {}

    for item in actuaciones_json:
        rad = item.get("radicado")
        if rad:
            if rad not in index_por_radicado:
                index_por_radicado[rad] = []
            index_por_radicado[rad].append(item)  # Guardamos EL JSON COMPLETO

    # --- Recorrer Excel ---
    for idx, row in df.iterrows():
        radicado_excel = str(row["RADICADO LARGO"]).strip()

        if not radicado_excel:
            continue

        # Radicados múltiples separados por coma
        lista_radicados = [r.strip() for r in radicado_excel.split(",") if r.strip()]

        json_finales = []

        # Buscar JSON completo por cada radicado
        for rad in lista_radicados:
            if rad in index_por_radicado:
                # Agregar TODOS los JSON asociados a ese radicado
                for obj in index_por_radicado[rad]:
                    json_finales.append(json.dumps(obj, ensure_ascii=False))

        # Guardar JSON en una sola celda, separado por comas
        if json_finales:
            df.at[idx, "ACTUACION"] = ", ".join(json_finales)

    # Guardar archivo actualizado
    output_path = "output/base/OBLIGACIONES_ACTUALIZADO.xlsx"
    df.to_excel(output_path, index=False)
    print(f"✔ Archivo actualizado guardado en: {output_path}")


if __name__ == "__main__":
    #update_radicados()
    update_actuaciones()
