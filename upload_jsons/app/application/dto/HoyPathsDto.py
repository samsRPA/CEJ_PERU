from datetime import datetime
from pathlib import Path
from pydantic import BaseModel


class HoyPathsDto(BaseModel):
    display: str
    slug: str
    json_dir:Path
    logs_file: Path
    hour: str
    minute: str

    @staticmethod
    def build() -> "HoyPathsDto":
        now = datetime.now()
        day = f"{now.day:02d}"
        month = f"{now.month:02d}"
        year = f"{now.year}"
        hour = f"{now.hour:02d}"
        minute = f"{now.minute:02d}"

        date_str_display = f"{day}/{month}/{year}"
        date_str_slug = f"{day}-{month}-{year}"

             # Carpeta raíz de output
        base_output = Path("/app/output")

     
        
        base_jsons= base_output/"jsons"/date_str_slug
        base_logs = base_output / "logs" / f"descarga_actuaciones.csv"

    
        for p in [base_jsons]:
            p.mkdir(parents=True, exist_ok=True)

        return HoyPathsDto(
            display=date_str_display,
            slug=date_str_slug,
            json_dir=base_jsons.resolve(),
            # revisar_dir=base_revisar.resolve(),
            logs_file=base_logs.resolve(),
            hour=hour,
            minute=minute
        )
