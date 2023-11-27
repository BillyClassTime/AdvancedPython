from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from services.rabbitMQServices import RabbitMQ
from services.securityServices import get_current_user

route = APIRouter() 

@route.get("/consumir")
async def consumir(str=Depends(get_current_user)):
    mensaje_recibidos = None
    rabbitmq = None
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
    except HTTPException as he:
        print(f"Excepcion HTTP consumiendo el mensaje: {he.detail}")
        return {"mensajes": []}
    finally:
        if rabbitmq is not None:
            await rabbitmq.close()

@route.post("/publicar/{mensaje}", response_model=dict)
async def publicar_mensaje(mensaje: str, current_user: str=Depends(get_current_user)):
    rabbitmq = None
    try:
        #print(f"Publicando mensaje: {mensaje}")
        if current_user is None:
            raise HTTPException(status_code=401, detail=f"usuario:{current_user}, no autorizado")
        #else:
        #    print(f"Usuario autenticado: {current_user}")
        rabbitmq = RabbitMQ()
        await rabbitmq.connect()
        await rabbitmq.publish_message(mensaje)
        return {"mensaje": f"Mensaje '{mensaje}' publicado correctamente en la cola."}
    except Exception as e:
        print(f"Excepción publicando el mensaje:{str(e)}")
        raise HTTPException(status_code=500, detail=f"publicando el mensaje:{str(e)}")
    finally:
        if rabbitmq is not None:
            await rabbitmq.close()

@route.get("/", response_class=RedirectResponse, status_code=302,include_in_schema=False)
async def redirect_to_docs():
    return "/docs"        