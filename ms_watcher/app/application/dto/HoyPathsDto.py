from datetime import datetime
from pathlib import Path
from pydantic import BaseModel


class HoyPathsDto(BaseModel):
  

    logs_file: Path


    @staticmethod
    def build() -> "HoyPathsDto":

        base_output = Path("/app/output")
        #base_output = Path("/output")

        # Subcarpetas dentro de output
  
        base_logs = base_output / "logs" / f"logs_expedientes.cvs"

    

        return HoyPathsDto(
       
            logs_file=base_logs.resolve(),
        
        )
