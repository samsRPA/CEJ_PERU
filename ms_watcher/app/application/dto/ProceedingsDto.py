from typing import Optional
from pydantic import BaseModel

class ProceedingsDto(BaseModel):
    nombre_completo:Optional[str] = None
   # identificacion_cliente:Optional[str] = None
    distrito_judicial: Optional[str] = None
    instancia: Optional[str] = None
    especialidad: Optional[str] = None
    annio: Optional[str] = None
    num_expediente: Optional[str] = None
    parte: Optional[str] = None
    radicado: Optional[str] = None
    demandante: Optional[str] = None
    parte_demandante: Optional[str] = None
    
    
