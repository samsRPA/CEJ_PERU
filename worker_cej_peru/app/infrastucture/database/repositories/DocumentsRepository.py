
import logging
import oracledb 
import json
import os
class DocumentsRepository():

    
    def __init__(self, table_car):
        self.table_car = table_car
        self.logger = logging.getLogger(__name__)


    async def insert_document(
        self, conn, fecha_notificacion: str, radicacion: str, consecutivo: int,
        ruta_s3: str, url_auto: str, origen: str, tipo_documento: str, fecha_registro_tyba:str
    ) -> bool:
        """
        Inserta un documento en CONTROL_AUTOS_RAMA_1 con las columnas básicas.
        """
        try:
            query = f"""
                INSERT INTO CONTROL_AUTOS_RAMA_1 (
                    FECHA_NOTIFICACION,
                    RADICACION,
                    CONSECUTIVO,
                    RUTA_S3,
                    URL_AUTO,
                    ORIGEN,
                    TIPO_DOCUMENTO,
                    FECHA_AUTO
                    
                ) VALUES (
                    TO_DATE(:fecha_notificacion, 'DD-MM-YYYY'),
                    :radicacion,
                    :consecutivo,
                    :ruta_s3,
                    :url_auto,
                    :origen,
                    :tipo_documento,
                    TO_DATE(:fecha_auto, 'DD/MM/YYYY HH24:MI:SS')
                    
                )
            
                
            """

            async with conn.cursor() as cursor:
                await cursor.execute(query, {
                        "fecha_notificacion": fecha_notificacion,
                        "radicacion": radicacion,
                        "consecutivo": consecutivo,
                        "ruta_s3": ruta_s3,
                        "url_auto": url_auto,
                        "origen": origen,
                        "tipo_documento": tipo_documento,
                        "fecha_auto":fecha_registro_tyba
                })

            

            return True

        except Exception as error:
            await conn.rollback()
            self.logger.error(f"❌ Error en insertar_documento_simple: {error}")
            return False



    async def exists_document(self, conn, data: dict) -> bool:
        """
        Verifica si existe un documento en la tabla CONTROL_AUTOS_RAMA_1 
        según la fecha de notificación, radicación y consecutivo.
        Retorna True si existe, False si no.
        """
        sql = """
            SELECT 1
            FROM CONTROL_AUTOS_RAMA_1
            WHERE FECHA_NOTIFICACION = :fecha_notificacion
            AND RADICACION = :radicacion
            AND CONSECUTIVO = :consecutivo
            FETCH FIRST 1 ROWS ONLY
        """

        binds = {
            "fecha_notificacion": data.get("FECHA_NOTIFICACION"),
            "radicacion": data.get("RADICACION"),
            "consecutivo": data.get("CONSECUTIVO"),
        }

        try:
          

            async with conn.cursor() as cursor:
                await cursor.execute(sql, binds)
                row = await cursor.fetchone()

            exists = row is not None

            # 🔹 Log de resultado
            if exists:
                self.logger.info(f"📄 Documento existente para RADICACION={binds['radicacion']}, fecha ={binds['fecha_notificacion']} consecutivo ={binds['consecutivo']}")
            else:
                f"CONSECUTIVO={binds['consecutivo']}"
                f"CONSECUTIVO={binds['consecutivo']}"
                self.logger.info(f"📄 No se encontró documento para RADICACION={binds['radicacion']} , fecha ={binds['fecha_notificacion']} consecutivo ={binds['consecutivo']}")

            return exists

        except Exception as err:
            self.logger.error(
                f"🚨 Error al verificar existencia de documento RADICACION={binds.get('radicacion')}: {err}",
                exc_info=True
            )
            raise



   
    async def get_max_consecutive(self, conn, data: dict) -> int:
        sql = f"""
            SELECT NVL(MAX(CONSECUTIVO), 0) AS MAX_CONSECUTIVO
            FROM {self.table_car}
            WHERE RADICACION = :RADICACION
              AND FECHA_NOTIFICACION = TO_DATE(:FECHA_NOTIFICACION, 'DD/MM/YYYY')
        """

        binds = {
            "RADICACION": data.get("RADICACION"),
            "FECHA_NOTIFICACION": data.get("FECHA_NOTIFICACION"),
        }

        # 🔹 Log de inicio
        self.logger.info(
            f"🔍 Obteniendo máximo consecutivo para RADICACION={binds['RADICACION']} "
            f"y FECHA_NOTIFICACION={binds['FECHA_NOTIFICACION']}"
        )

        try:
            max_consecutivo=None
   
            async with conn.cursor() as cursor:
                await cursor.execute(sql, binds)
                row = await cursor.fetchone()
                max_consecutivo=row[0] if row else None
                    
            
            if not isinstance(max_consecutivo, (int, float)):
                raise ValueError(f"El resultado del max_consecutivo no es numérico: {max_consecutivo}")
                
  

            # 🔹 Log de resultado
            self.logger.info(
                f"📄 Máximo consecutivo obtenido para RADICACION={binds['RADICACION']}: {max_consecutivo}"
            )

            return max_consecutivo

        except Exception as err:
            self.logger.error(
                f"🚨 Error al obtener máximo consecutivo para RADICACION={binds['RADICACION']}: {err}",
                exc_info=True
            )
            raise err
