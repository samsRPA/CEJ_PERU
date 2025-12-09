

import oracledb
import logging
class CargaMasivaCJRepository:
    def __init__(self, schema="LITI.INSERT_MASIVOS"):
        self.schema = schema

    def insert_masivo(self, conn, tipo_cargue: str, json_content: str):
        """
        Ejecuta el procedimiento de cargue masivo en Oracle.
        
        :param conn: Conexión activa a Oracle
        :param tipo_cargue: Tipo de cargue (ej: "CJ_ECUADOR" o "CJ_ACTORES")
        :param json_content: Contenido JSON en formato string
        :return: Mensaje devuelto por el procedimiento
        """
        try:
            plsql = f"""
                BEGIN
                    LITI.INSERT_MASIVOS.CARGUE_MASIVO(
                        P_TIPO_CARGUE => :tipo,
                        P_CLOB        => :jsonData,
                        P_MESSAGE     => :mensaje
                    );
                END;
            """

            with conn.cursor() as cursor:
                    # OUT param como VARCHAR2(4000)
                mensaje = cursor.var(oracledb.DB_TYPE_VARCHAR, size=4000)
                    
                    # JSON como CLOB
                json_clob = cursor.var(oracledb.DB_TYPE_CLOB)
                json_clob.setvalue(0, json_content)

                cursor.execute(plsql, {
                        "tipo": tipo_cargue,
                        "jsonData": json_clob,
                        "mensaje": mensaje
                    })

                conn.commit()
                logging.info(f"✅ Mensaje devuelto: {mensaje.getvalue()}")
                return True

        except Exception as error:
            conn.rollback()
            logging.error(f"❌ Error inesperado: {error}")
            return False
            

    