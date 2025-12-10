import pandas as pd
import logging
from app.domain.interfaces.IGetProceedingsService import IGetProceedingsService
from app.application.dto.ProceedingsDto import ProceedingsDto
import json

from app.domain.interfaces.IDataBase import IDataBase
from app.infrastucture.database.repositories.KeyCEJRepository import KeyCEJRepository

class GetProceedingsService(IGetProceedingsService):

    

    def __init__(self,db:IDataBase,repository:KeyCEJRepository):
        self.db = db
        self.repository = repository
        self.logger = logging.getLogger(__name__)

    async def get_proceedings(self):
        conn = None
        try:
            conn = await self.db.acquire_connection()
            raw_keys = await self.repository.get_keys_cej(conn)

            proceedings_list = []

            for row in raw_keys:
                # row = (PROCESO_ID, INSTANCIA_RADICACION, ..., DEMANDADO)

                instancia_radicacion = self._clean(row[1])
                demandado_raw = self._clean(row[6])

                # Extraer apellidos igual que en Excel
                demandado_apellidos = self._extract_surnames(demandado_raw)

                dto = ProceedingsDto(
                    nombre_completo="",
                    distrito_judicial="",
                    instancia="",
                    especialidad="",
                    annio="",
                    num_expediente="",
                    parte=demandado_apellidos,
                    radicado=instancia_radicacion
                )
                proceedings_list.append(dto)
                 # Guardar JSON
                 
            json_ready = [dto.model_dump() for dto in proceedings_list]
            with open("/app/output/base/proceedings.json", "w", encoding="utf-8") as f:
                json.dump(json_ready, f, ensure_ascii=False, indent=4)

            return proceedings_list

    

        finally:
            if conn:
                await self.db.release_connection(conn)

            
        
        
    def get_proceedings_by_excel(self): 
        try: 
            excel_path = "/app/output/base/OBLIGACIONES_ACTUALIZADO Y REVISADO MANUAL.xlsx" 
            df = pd.read_excel(excel_path) 

            # Normalizar columnas
            df.columns = df.columns.str.strip().str.upper() 

            proceedings_list = [] 

            for _, row in df.iterrows():

                distrito_judicial = self._clean(row["CIUDAD"])
                especialidad = self._clean(row["ESPECIALIDAD"])

                # AÑO sin .0 
                annio_raw = row["AÑO"]
                if pd.isna(annio_raw): 
                    annio = "" 
                else: 
                    annio = str(int(float(annio_raw))) 

                # EXP JUDICIAL → tomar número antes del guión
                raw_exp = self._clean(row["EXP JUDICIAL"])
                num_expediente = raw_exp.split("-")[0].strip() if raw_exp else ""

                # NOMBRE CLIENTE → EXTRAER APELLIDOS 
                raw_name = self._clean(row["NOMBRE CLIENTE"])
                nombre_completo = raw_name
                parte = self._extract_surnames(raw_name)

                radicado = self._clean(row["RADICADO LARGO"])
                instancia = self._clean(row["INSTANCIA"])

                dto = ProceedingsDto(
                    nombre_completo=nombre_completo,
                    distrito_judicial=distrito_judicial,
                    instancia=instancia,
                    especialidad=especialidad,
                    annio=annio,
                    num_expediente=num_expediente,
                    parte=parte,
                    radicado=radicado
                )

                proceedings_list.append(dto)

            # Guardar JSON
            json_ready = [dto.model_dump() for dto in proceedings_list]
            with open("/app/output/base/proceedings.json", "w", encoding="utf-8") as f:
                json.dump(json_ready, f, ensure_ascii=False, indent=4)

            return proceedings_list

        except Exception as error: 
            self.logger.exception(f"Error al procesar Excel: {error}") 
            raise


    def _clean(self, value):
        # Si llega una Serie → tomar primer elemento
        if isinstance(value, pd.Series):
            value = value.iloc[0] if not value.empty else ""

        if pd.isna(value):
            return ""

        value = str(value).strip()
        return " ".join(value.split())



    def _extract_surnames(self,nombre):
        partes = nombre.split() 

        if len(partes) == 1:
            return partes[0]

        if len(partes) == 2:
            return partes[1]

        if len(partes) == 3:
            return " ".join(partes[-2:])

        # 4 palabras o más → todo después de las primeras dos
        return " ".join(partes[2:])
