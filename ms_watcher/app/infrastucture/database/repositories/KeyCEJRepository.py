import asyncio


class KeyCEJRepository:
    def __init__(self):
        pass

    async def get_keys_cej(self, conn):
        try:
            query = f""" 
            SELECT REGEXP_REPLACE(PI.INSTANCIA_RADICACION, '[^0-9]', '') AS INSTANCIA_RADICACION
                FROM DESPACHOS D
                    JOIN LOCALIDADES L ON D.LOCALIDAD_ID = L.LOCALIDAD_ID
                    JOIN PROCESOS_INSTANCIAS PI ON PI.DESPACHO_ID = D.DESPACHO_ID
                WHERE L.LOCALIDAD_ID IN (
                        SELECT LOCALIDAD_ID
                        FROM LOCALIDADES
                        CONNECT BY PRIOR LOCALIDAD_ID = LOCALIDAD_PADRE
                        START WITH LOCALIDAD_ID = 239
                )
            """
            
            async with conn.cursor() as cursor:
                await cursor.execute(query)
                # extraemos solo el primer elemento de cada tupla
                return [row[0] for row in await cursor.fetchall()]
         
        except Exception as error:
            raise error
