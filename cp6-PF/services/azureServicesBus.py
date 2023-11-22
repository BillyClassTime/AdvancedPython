import asyncio
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage


NAMESPACE_CONNECTION_STR = "CONNECTION STRING"


class azureServicesBus():
    def __init__(self): 
        self.connectionString=NAMESPACE_CONNECTION_STR
        self.client = ServiceBusClient.from_connection_string(
            conn_str=self.connectionString,
            logging_enable=True)
        
    async def enviar_mensaje_a_cola(self, mensaje_content, cola_nombre):
        try:
            sender = self.client.get_queue_sender(queue_name=cola_nombre)
            async with sender:
                message = ServiceBusMessage(mensaje_content)
                await sender.send_messages(message)
                return {"status": "Sent a single message"}
        except Exception as e:
            return {"status": "Failed to send message", "error": str(e)}


    async def recibir_mensaje_de_cola(self, cola_nombre):
        try:
            receiver = self.client.get_queue_receiver(queue_name=cola_nombre)
            async with receiver:
                messages = await receiver.receive_messages(max_message_count=1,
                                                           max_wait_time=5)
                if messages:
                    # Decode the bytes to a string
                    message_body = "".join(b.decode('utf-8') for b in messages[0].body)
                    # Complete the message to remove it from the queue
                    await receiver.complete_message(messages[0])
                    return {"message": message_body}
                else:
                    return {"message": "No hay mensajes"}    
        except Exception as e:
            return {"status": "Failed to receive message", "error": str(e)}