import asyncio

import aio_pika
from typing import Callable


from app.domain.interfaces.IRabbitMQConsumer import IRabbitMQConsumer
from app.domain.interfaces.IScrapperService import IScrapperService
import logging

from app.application.dto.ProceedingsRequestDto import ProceedingsRequestDto


class RabbitMQConsumer(IRabbitMQConsumer):

    def __init__(self, host: str, port: int, pub_queue_name: str, prefetch_count: int,
                 scrapper_service: Callable[[str], IScrapperService], user, password):
        self.host = host
        self.host = host
        self.port = port
        self.pub_queue_name = pub_queue_name
        self.prefetch_count = prefetch_count
        self.scrapper_service = scrapper_service
        self.queue: aio_pika.Queue | None = None
        self.channel: aio_pika.Channel | None = None
        self.connection: aio_pika.RobustConnection | None = None
        self.user = user
        self.password = password

    async def connect(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                login=self.user,
                password=self.password,
                timeout=10,               # Tiempo máximo de conexión
                heartbeat=120,             # Heartbeat cada 60s (debe ser >= al del broker)

            )
            
            self.channel = await self.connection.channel()

            await self.channel.set_qos(prefetch_count=self.prefetch_count)
            self.queue = await self.channel.declare_queue(
                self.pub_queue_name, durable=True
            )
            logging.info("✅ Conectado a RabbitMQ - Consumer")


        except Exception as error:
            logging.error(f"❌ Error conectando al consumer: {error}")
            raise error

    async def callback(self, message: aio_pika.IncomingMessage):
        async with message.process(ignore_processed=True):
            try:

                raw_body = message.body.decode()
              
                request = ProceedingsRequestDto.fromRaw(raw_body)
               

                # Crear servicio y correr scrapper
                service = self.scrapper_service(request)
                await service.runScrapper()

            except Exception as e:
                logging.error(f"❌ Error procesando mensaje: {e}")
                try:
                    await message.nack(requeue=False)
                except aio_pika.exceptions.MessageProcessError:
                    logging.warning("⚠️ Intento de NACK en un mensaje ya procesado.")

    async def startConsuming(self):
        if not self.channel or not self.queue:
            logging.info("📡 Conexión no establecida. Conectando...")
            await self.connect()

        await self.queue.consume(self.callback)
        logging.info("🎧 Esperando mensajes...")

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("👋 Interrupción manual detectada.")
        finally:
            if self.connection:
                await self.connection.close()
                logging.info("🔌 Conexión a RabbitMQ cerrada.")



