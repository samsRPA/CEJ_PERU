import json
from typing import Optional
from pydantic import BaseModel, ValidationError  # usa el de pydantic

class ProceedingsRequestDto(BaseModel):
    nombre_completo:Optional[str] = None
    #identificacion_cliente:Optional[str] = None
    distrito_judicial: Optional[str] = None
    instancia: Optional[str] = None
    especialidad: Optional[str] = None
    annio: Optional[str] = None
    num_expediente: Optional[str] = None
    parte: Optional[str] = None
    radicado: Optional[str] = None

    @classmethod
    def fromRaw(cls, rawBody: str):
        try:
            data = json.loads(rawBody)
            return cls(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(f"Invalid scrapper request data: {e}")
