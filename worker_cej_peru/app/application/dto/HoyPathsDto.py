from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from pydantic import BaseModel

class HoyPathsDto(BaseModel):
    display: str
    slug: str
    logs_file: Path


    @staticmethod
    def build() -> "HoyPathsDto":
        now = datetime.now(ZoneInfo("America/Bogota"))
        day = f"{now.day:02d}"
        month = f"{now.month:02d}"
        year = f"{now.year}"
     

        date_str_display = f"{day}/{month}/{year}"
        date_str_slug = f"{day}-{month}-{year}"

             # Carpeta raíz de output
        
        base_output = Path("/app/output")
        #base_output = Path("/output")

        # Subcarpetas dentro de output
       
        base_logs = base_output / "logs" / f"{date_str_slug}_logs_documents.csv"
     
   
        return HoyPathsDto(
            display=date_str_display,
            slug=date_str_slug,
            logs_file=base_logs.resolve(),
        
        )
