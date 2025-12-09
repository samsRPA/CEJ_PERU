import logging
import oracledb

from app.domain.interfaces.IDataBase import IDataBase


class OracleDB(IDataBase):
    def __init__(self, db_user: str, db_password: str, db_host: str, db_port: int, db_service_name: str):
        self._db_user = db_user
        self._password = db_password
        self._host = db_host
        self._port = db_port
        self._service_name = db_service_name
        self._pool = None
        self.logger = logging.getLogger(__name__)

    @property
    def is_connected(self) -> bool:
        return self._pool is not None

    async def connect(self) -> None:
        try:
            dsn = f"{self._host}:{self._port}/{self._service_name}"
            self._pool =  oracledb.create_pool_async(   
                user=self._db_user,
                password=self._password,
                dsn=dsn,
                min=1,
                max=3,
                increment=1,
                getmode=oracledb.POOL_GETMODE_WAIT,
                homogeneous=True,
            )
            self.logger.info("✅ Pool de Oracle creado exitosamente.")
        except Exception as error:
            self.logger.error(f"❌ Error al crear el pool de Oracle: {error}")
            raise error

    async def acquire_connection(self):
        if not self._pool:
            raise Exception("⚠️ Pool no inicializado, llama a connect primero")
        conn = await self._pool.acquire()
        return conn

    async def release_connection(self, conn):
        try:
            await conn.rollback()
        except Exception:
            pass
        finally:
            await self._pool.release(conn)

    async def commit(self, conn):
        try:
            await conn.commit()
        except Exception as error:
            self.logger.error(f"❌ Error en commit: {error}")
            raise error

    async def close_connection(self):
        if self._pool:
            await self._pool.close()
            self._pool = None
            self.logger.info("🔌 Conexión a Oracle cerrada correctamente.")
