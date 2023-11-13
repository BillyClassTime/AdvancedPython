#pip install fastapi, aio-pika, uvicorn
from fastapi import FastAPI, HTTPException
import aio_pika
from fastapi.responses import JSONResponse

class RabbitMQ:
    def __init__(self):
        self.connection_string = 'amqp://manager:P455w0rd1234@172.191.110.21/'
        self.connection = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.connection_string)
        except aio_pika.exceptions.AMQPError as e:
            raise HTTPException(status_code=500, 
                                detail=f"Error al conectar con RabbitMQ: {str(e)}")

    async def publish_message(self, mensaje):
        if not self.connection:
            await self.connect()
        try:
            async with self.connection.channel() as channel:
                queue = await channel.declare_queue('mi_cola')
                await channel.default_exchange.publish(
                    aio_pika.Message(body=mensaje.encode()),
                    routing_key='mi_cola',timeout=30
                )
        except aio_pika.exceptions.AMQPError as e:
            errorMensaje="Error al publicar mensaje en RabbitMQ"
            raise HTTPException(status_code=500, 
                                detail=f"{errorMensaje}: {str(e)}")

    async def consume_messages(self, callback):
        if not self.connection:
            await self.connect()
        try:
            mensajes_recibidos = []
            async with self.connection.channel() as channel:
                queue = await channel.declare_queue('mi_cola')
                async def on_message(message):
                    async with message.process():
                        mensajes_recibidos.append(message.body.decode())
                await queue.consume(on_message)
            await callback(mensajes_recibidos)
        except aio_pika.exceptions.AMQPError as e:
            errorMensaje="Error al publicar mensaje en RabbitMQ"
            raise HTTPException(status_code=500, 
                                detail=f"{errorMensaje}: {str(e)}")

    async def close(self):
        if self.connection:
            await self.connection.close()

app = FastAPI()

@app.get("/consumir")
async def consumir_mensaje():
    mensaje_recibidos = None
    try:
        async def callback(mensajes):
            print(f"Recibidos mensajes: {mensajes}")
            nonlocal mensaje_recibidos
            mensaje_recibidos = mensajes
        rabbitmq = RabbitMQ()
        await rabbitmq.connect()
        await rabbitmq.consume_messages(callback)
        if mensaje_recibidos is not None and len(mensaje_recibidos) > 0:
            return {"mensajes": mensaje_recibidos}
        else:
            raise HTTPException(status_code=404, detail="No hay mensajes en la cola")
        #curl -X GET "http://localhost:puerto/consumir"
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"consumiendo el mensaje:{str(e)}") 
    finally:
        await rabbitmq.close()

@app.post("/publicar/{mensaje}", response_model=dict)
async def publicar_mensaje(mensaje: str):
    try:
        rabbitmq = RabbitMQ()
        await rabbitmq.connect()
        await rabbitmq.publish_message(mensaje)
        return {"mensaje": f"Mensaje '{mensaje}' publicado correctamente en la cola."}
        #curl -X POST "http://localhost:puerto/publicar/hola"
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"publicando el mensaje:{str(e)}")
    finally:
        await rabbitmq.close()

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Error interno del servidor"}
    )
    
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)