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
        
    def get_proceedings(self): 
        try: 
            excel_path = "/app/output/base/OBLIGACIONES_ACTUALIZADO Y REVISADO MANUAL.xlsx" 
            df = pd.read_excel(excel_path) 
            df.columns = df.columns.str.strip().str.upper() 
            proceedings_list = [] 
            for _, row in df.iterrows(): 
                distrito_judicial = self._clean(row.get("CIUDAD"))
                especialidad = self._clean(row.get("ESPECIALIDAD")) 
                # AÑO sin .0 
                annio_raw = row.get("AÑO") 
                if pd.isna(annio_raw): 
                    annio = "" 
                else: 
                    annio = str(int(float(annio_raw))) 
                # EXP JUDICIAL 
                raw_exp = self._clean(row.get("EXP JUDICIAL")) 
                num_expediente = raw_exp.split("-")[0].strip() if raw_exp else ""
                # NOMBRE CLIENTE → EXTRAER APELLIDOS 
                raw_name = self._clean(row.get("NOMBRE CLIENTE")) 
                nombre_completo=raw_name 
                parte = self._extract_surnames(raw_name) 
                radicado = self._clean(row.get("RADICADO LARGO"))
                instancia= self._clean(row.get("INSTANCIA")) 
                
                dto = ProceedingsDto( nombre_completo=nombre_completo, distrito_judicial=distrito_judicial,
                                     instancia=instancia, especialidad=especialidad, annio=annio, num_expediente=num_expediente,
                                     parte=parte, radicado=radicado, ) 
                proceedings_list.append(dto) 
                
            json_ready = [dto.model_dump() for dto in proceedings_list]
            with open("/app/output/base/proceedings.json", "w", encoding="utf-8") as f:
                json.dump(json_ready, f, ensure_ascii=False, indent=4) 
                
            return proceedings_list 
        except Exception as error: 
            self.logger.exception(f"Error al procesar Excel: {error}") 
            raise

    def _clean(self, value):
        if pd.isna(value):
            return ""
        value = str(value).strip()
        value = " ".join(value.split())  # <-- elimina espacios internos
        return value



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
