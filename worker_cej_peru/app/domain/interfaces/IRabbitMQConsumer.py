import aio_pika

from abc import ABC, abstractmethod

class IRabbitMQConsumer(ABC):

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def callback(self, message: aio_pika.IncomingMessage):
        pass

    @abstractmethod
    async def startConsuming(self):
        pass