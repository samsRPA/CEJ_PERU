import json
import logging
import aio_pika

from app.domain.interfaces.IRabbitMQProducer import IRabbitMQProducer


class RabbitMQProducer(IRabbitMQProducer):

    def __init__(self, host, port, pub_queue_name , user, password):
        self.host = host
        self.port = port
        self.pub_queue_name = pub_queue_name
        self.user= user
        self.password = password
        self.connection = None
        self.channel = None

    async def connect(self) -> None:
        try:
            self.connection = await aio_pika.connect_robust(
                host=self.host,
                port=self.port,
                timeout=5,
                login=self.user,
                password=self.password,
            )
            self.channel = await self.connection.channel()
            await self.channel.declare_queue(self.pub_queue_name, durable=True)
         
            logging.info("✅ Conectado a RabbitMQ - Producer")

        except Exception as error:
            logging.error(f"❌ Error conectando al Producer: {error}")
            raise error

    async def publishMessage(self, message):
        try:
            body = json.dumps(message).encode()
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT
                ),
                routing_key=self.pub_queue_name,
            )
            logging.info(f"📤 Mensaje enviado a {self.pub_queue_name}")
        except Exception as error:
            logging.exception("❌ Error enviando mensaje")
            raise error

    async def close(self) -> None:
        if self.connection:
            await self.connection.close()
            logging.info("🔌 Conexión con RabbitMQ cerrada")
