import os
import aio_pika
from custom_exceptions.rabbitMQExceptions import RabbitMQError
from app_core.utils.messagetobase64 import conform_message_request, conform_message_response
from dotenv import load_dotenv
import json

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
        self.exchange_name = 'analysis_exchange'
        self.connection = None
    
    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.connection_string)
        except aio_pika.exceptions.AMQPError as e:
            raise RabbitMQError(f"Error al conectar con RabbitMQ: {str(e)}")
    
    async def __create_channel(self):
        return await self.connection.channel()

    async def __declare_queue(self, channel, queue_name):
        return await channel.declare_queue(queue_name, durable=True)

    async def __publish_message(self, channel, exchange, routing_key, message):
        await exchange.publish(
            aio_pika.Message(json.dumps(message).encode(),
                             delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                             expiration=360000),
            routing_key=routing_key, timeout=30
        )
                
    async def publish_message_request(self, mensaje):
        if not self.connection:
            await self.__connect()
        try:
            message_request = conform_message_request(mensaje)
            id_request = message_request['id']
            queue_name = f"queue_{id_request}_request"
            routing_key_name = f"routing_key_{id_request}_request"

            channel = await self.__create_channel()
            exchange = await channel.declare_exchange(self.exchange_name, 
                                                      aio_pika.ExchangeType.DIRECT, durable=True)
            queue = await self.__declare_queue(channel, queue_name)
            await queue.bind(exchange, routing_key=routing_key_name)
            await self.__publish_message(channel, exchange, routing_key_name, message_request)
        
        except aio_pika.exceptions.AMQPError as e:
            errorMensaje="Error al publicar mensaje de request en RabbitMQ"
            print(f"{errorMensaje}: {e}")
            raise RabbitMQError(f"{errorMensaje}: {e}")
        return id_request
            
    async def publish_message_response(self, id_request, message):
        if not self.connection:
            await self.__connect()
        try:
            response_message = conform_message_response(id_request, message)                            
            queue_name = f"queue_{id_request}_response"
            routing_key_name = f"routing_key_{id_request}_response"
                        
            channel = await self.__create_channel()
            exchange = await channel.declare_exchange(self.exchange_name, 
                                                      aio_pika.ExchangeType.DIRECT, durable=True)
            queue = await self.__declare_queue(channel, queue_name)
            await queue.bind(exchange, routing_key=routing_key_name)
            await self.__publish_message(channel, exchange, routing_key_name, response_message)
    
        except aio_pika.exceptions.AMQPError as e:
            errorMensaje="Error al publicar mensaje de response en RabbitMQ"
            print(f"{errorMensaje}: {e}")
            raise RabbitMQError(f"{errorMensaje}: {e}")
        return id_request          

    async def consume_message_response(self, id_request, callback):
        if not self.connection:
            await self.__connect()
        try:
            queue_name = f"queue_{id_request}_response"
            routing_key_name = f"routing_key_{id_request}_response"
            channel = await self.__create_channel()
            exchange = await channel.declare_exchange(self.exchange_name, 
                                                      aio_pika.ExchangeType.DIRECT, durable=True)
            queue = await self.__declare_queue(channel, queue_name)
            await queue.bind(exchange, routing_key=routing_key_name)
            await queue.consume(callback, no_ack=True)
        except aio_pika.exceptions.AMQPError as e:
            errorMensaje="Error al consumir mensaje de response en RabbitMQ"
            print(f"{errorMensaje}: {e}")
            raise RabbitMQError(f"{errorMensaje}: {e}")    

    async def consume_message_request(self, id_request,callback):
        if not self.connection:
            await self.__connect()
        try:
            queue_name = f"queue_{id_request}_request"
            routing_key_name = f"routing_key_{id_request}_request"
            channel = await self.__create_channel()
            exchange = await channel.declare_exchange(self.exchange_name, 
                                                      aio_pika.ExchangeType.DIRECT, durable=True)
            queue = await self.__declare_queue(channel, queue_name)
            await queue.bind(exchange, routing_key=routing_key_name)
            await queue.consume(callback, no_ack=True)
        except aio_pika.exceptions.AMQPError as e:
            errorMensaje="Error al consumir mensaje de request en RabbitMQ"
            print(f"{errorMensaje}: {e}")
            raise RabbitMQError(f"{errorMensaje}: {e}")
                    
    async def close(self):
        if self.connection:
            await self.connection.close()                