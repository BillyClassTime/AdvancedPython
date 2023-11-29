import os
import aio_pika
from custom_exceptions.rabbitMQExceptions import RabbitMQError
from dotenv import load_dotenv

load_dotenv() # Carga las variables de entorno del fichero .env	

class RabbitMQ:
    def __init__(self):
        rabbitmq_host = os.getenv("RABBITMQ_HOST")
        rabbitmq_port = os.getenv("RABBITMQ_PORT")
        rabbitmq_user = os.getenv("RABBITMQ_USERNAME")
        rabbitmq_password = os.getenv("RABBITMQ_PASSWORD")
        rabbitmq_vhost = os.getenv("RABBITMQ_VHOST").replace("\\","") if os.getenv("RABBITMQ_VHOST") else None
        self.connection_string = f'amqp://{rabbitmq_user}:{rabbitmq_password}@{rabbitmq_host}:{rabbitmq_port}/{rabbitmq_vhost}'
        #self.connection_string = 'amqp://usuario:clave@hostvhost'
        self.connection = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.connection_string)
        except aio_pika.exceptions.AMQPError as e:
            raise RabbitMQError(f"Error al conectar con RabbitMQ: {str(e)}")

    async def publish_message(self, mensaje):
        if not self.connection:
            await self.connect()
        try:
            async with self.connection.channel() as channel:
                queue = await channel.declare_queue('mis_mensajes',durable=True)
                #channel.enable_publisher_confirms()
                await channel.default_exchange.publish(
                    aio_pika.Message(body=mensaje.encode(),
                                     delivery_mode=aio_pika.DeliveryMode.PERSISTENT, # El mensaje se guarda en disco
                                     # Si no se extablece expiration, el mensaje no caduca
                                     expiration=360000), # Tiempo en milisegundos antes de que el mensaje
                    routing_key='mis_mensajes',timeout=30
                )
                #channel.publisher_confirms()
        except aio_pika.exceptions.AMQPError as e:
            errorMensaje="Error al publicar mensaje en RabbitMQ"
            print(f"{errorMensaje}: {str(e)}")
            raise RabbitMQError(f"{errorMensaje}: {str(e)}")

    async def consume_messages(self, callback):
        if not self.connection:
            await self.connect()
        try:
            mensajes_recibidos = []
            async with self.connection.channel() as channel:
                queue = await channel.declare_queue('mis_mensajes',durable=True)
                async def on_message(message):
                    try:
                        #async with message.process(): # El mensaje se marca como procesado
                        mensajes_recibidos.append(message.body.decode())
                    except Exception as e:
                        raise RabbitMQError(f"Error al procesar mensaje: {str(e)}")
                await queue.consume(on_message)
            await callback(mensajes_recibidos)
        except aio_pika.exceptions.AMQPError as e:
            errorMensaje="Error al consumir mensaje en RabbitMQ"
            raise RabbitMQError(f"{errorMensaje}: {str(e)}")

    async def close(self):
        if self.connection:
            await self.connection.close()