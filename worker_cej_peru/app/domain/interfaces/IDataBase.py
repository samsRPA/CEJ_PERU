from abc import ABC, abstractmethod


class IDataBase(ABC):

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def acquire_connection(self):
        pass

    @abstractmethod
    async def release_connection(self, conn):
        pass

    @abstractmethod
    async def commit(self, conn):
        pass

    @abstractmethod
    async def close_connection(self, conn):
        pass
