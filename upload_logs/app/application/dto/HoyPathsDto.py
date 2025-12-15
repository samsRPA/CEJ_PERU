from datetime import datetime
from pathlib import Path
from pydantic import BaseModel
from zoneinfo import ZoneInfo 

class HoyPathsDto(BaseModel):
    display: str
    slug: str
    estados_dir: Path
    capturas_dir: Path
    # revisar_dir: Path
    logs_file: Path
    img_dir: Path
    hour: str
    minute: str
    base_output:Path

    @staticmethod
    def build() -> "HoyPathsDto":
        now = datetime.now(ZoneInfo("America/Bogota"))
        day = f"{now.day:02d}"
        month = f"{now.month:02d}"
        year = f"{now.year}"
        hour = f"{now.hour:02d}"
        minute = f"{now.minute:02d}"

        date_str_display = f"{day}/{month}/{year}"
        date_str_slug = f"{day}-{month}-{year}"

             # Carpeta raíz de output
        base_output = Path("/app/output")

        # Subcarpetas dentro de output
        base_estados = base_output / "estados" / date_str_slug
        base_capturas = base_output / "capturas" / date_str_slug
        base_logs = base_output / "logs" / f"{date_str_slug}_descarga_estados.csv"
        base_img = base_output / "img"
        """
        for p in [base_estados, base_capturas, base_revisar, base_img]:
            p.mkdir(parents=True, exist_ok=True)
        """
        for p in [base_estados, base_capturas, base_img]:
            p.mkdir(parents=True, exist_ok=True)

        return HoyPathsDto(
            display=date_str_display,
            slug=date_str_slug,
            estados_dir=base_estados.resolve(),
            capturas_dir=base_capturas.resolve(),
            # revisar_dir=base_revisar.resolve(),
            logs_file=base_logs.resolve(),
            img_dir=base_img.resolve(),
            hour=hour,
            minute=minute,
            base_output=base_output.resolve()
        )
