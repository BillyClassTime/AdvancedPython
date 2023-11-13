import sys
import aio_pika
from fastapi import FastAPI, HTTPException

class PatronSubscritorPublicador:
    def __init__(self, connection_string='amqp://manager:P455w0rd1234@172.191.110.21/'):
        self.connection_string = connection_string
        self.connection = None

    async def __aenter__(self):
        try:
            self.connection = await aio_pika.connect_robust(self.connection_string)
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
        finally:
            return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        try:
            if self.connection:
                await self.connection.close()
        except Exception as e:
            print(f"Error: {str(e)}")
            sys.exit(1)
        finally:
            return self

    async def publish_message(self, message,queue_name='queue1'):
        async with self.connection.channel() as channel:
            exchange = await channel.declare_exchange(queue_name, 
                                                      type=aio_pika.ExchangeType.FANOUT)
            queue = await channel.declare_queue(queue_name, durable=True,exclusive=False)
            await queue.bind(exchange)
            await exchange.publish(aio_pika.Message(body=message.encode()), routing_key='')

    async def consume_messages(self, queue_name='queue1'):
        mensajes_recibidos = []
        async with self.connection.channel() as channel:
            try:
                exchange = await channel.declare_exchange(queue_name, 
                                                          type=aio_pika.ExchangeType.FANOUT)
                queue = await channel.declare_queue(queue_name, exclusive=False,durable=True)
                await queue.bind(exchange)
                async def on_message(message):
                    try:
                        async with message.process():
                            mensajes = message.body.decode()
                            print(f"en on_message de la funcion consume:{mensajes}")
                            mensajes_recibidos.append(mensajes)
                    except Exception as e:
                        print(f"Error on messages: {str(e)}")
                await channel.set_qos(prefetch_count=1)
                await queue.consume(on_message)
            except Exception as e:
                print(f"Error: {str(e)}")
            return mensajes_recibidos
    
app = FastAPI()

async def publish_message(message):
    async with PatronSubscritorPublicador() as pubsub:
        await pubsub.publish_message(message)

@app.post("/emitir/{message}")
async def emitir(message: str):
    try:
        await publish_message(message)
        return {"status": "Message sent successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

async def handle_messages(message):
        return message
        
async def consume_message(queue_name='queue1'):
    async with PatronSubscritorPublicador() as pubsub:
        return await pubsub.consume_messages(queue_name=queue_name)

@app.get("/recibir/{queue_name}")
async def recibir(queue_name: str):
    try:
        mensajes_recibidos = await consume_message(queue_name)
        return {"status": "Message received successfully.","data": mensajes_recibidos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
