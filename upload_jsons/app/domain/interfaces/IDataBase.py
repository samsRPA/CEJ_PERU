from abc import ABC, abstractmethod


class IDataBase(ABC):

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        pass

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def acquire_connection(self):
        pass

    @abstractmethod
    def release_connection(self, conn):
        pass

    @abstractmethod
    def commit(self, conn):
        pass

    @abstractmethod
    def close_connection(self, conn):
        pass
