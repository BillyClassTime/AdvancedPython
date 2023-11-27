from fastapi import APIRouter, HTTPException
from services.manageServices import RabbitMQ
from fastapi.responses import JSONResponse, RedirectResponse

class CustomAPIRouter(APIRouter):
    async def exception_handler(self, request, exc):
        return JSONResponse(status_code=500, content={"message": "Error interno del servidor"})

route = CustomAPIRouter() 

@route.get("/consumir")
async def consumir():
    mensaje_recibidos = None
    try:
        async def callback(mensajes):
            #print(f"Recibidos mensajes: {mensajes}")
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

@route.post("/publicar/{mensaje}", response_model=dict)
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

@route.get("/", response_class=RedirectResponse, status_code=302,include_in_schema=False)
async def redirect_to_docs():
    return "/docs"  