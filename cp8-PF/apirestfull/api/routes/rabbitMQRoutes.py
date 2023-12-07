import asyncio
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
import json

from services.rabbitMQServices import RabbitMQ
from services.securityServices import get_current_user
from app_core.utils.messagetobase64 import is_valid_uuid

route = APIRouter() 


from fastapi import Body

@route.post("/publicar_mensaje_solicitud", response_model=dict, tags=["RabbitMQ"] ,summary="Publicar mensaje de solicitud")
async def publicar_mensaje_solicitud(mensaje: dict = Body(...), current_user: str=Depends(get_current_user)):
    rabbitmq = None
    try:
        if current_user is None:
            raise HTTPException(status_code=401, detail=f"usuario:{current_user}, no autorizado")
        rabbitmq = RabbitMQ()
        await rabbitmq.connect()
        id_request = await rabbitmq.publish_message_request(mensaje)
        return {f"id": id_request,"estado": "enviado para análisis"}
    except Exception as e:
        print(f"Excepción publicando el mensaje:{e}")
        return {"id": None, "estado": f"error:{e}, sending"}
    finally:
        if rabbitmq is not None:
            await rabbitmq.close()

@route.get("/consumir_mensaje_solicitud/{id_request}", response_model=dict, tags=["RabbitMQ"] ,summary="Consumir mensaje de solicitud")
async def consumir_mensaje_solicitud(id_request: str, str=Depends(get_current_user)):
    if id_request is None or len(id_request) == 0 or not is_valid_uuid(id_request):
        return {"id":"no puede ser nulo","estado": "Debe realizar una petición con un id de solicitud válido"}
    mensaje_solicitud_future = asyncio.Future()
    rabbitmq = None
    try:
        rabbitmq = RabbitMQ()
        await rabbitmq.connect()

        async def callback(mensaje):
            if mensaje is not None and mensaje.body is not None and len(mensaje.body) > 0:
                print(f"Recibidos mensajes: {mensaje.body}")
                mensaje_solicitud_future.set_result(mensaje.body.decode("utf-8"))
            else:
                mensaje_solicitud_future.set_result("{}")

        await rabbitmq.consume_message_request(id_request,callback)
        mensaje_solicitud = await asyncio.wait_for(mensaje_solicitud_future, timeout=5) #espera 5 segundos
        if mensaje_solicitud is None:
            return {"id":id_request,"estado": "no se recibio ningun mensaje"}
        try:
            mensaje = json.loads(mensaje_solicitud)
            mensaje["estado"] = "analizando datos"
            return mensaje
        except json.JSONDecodeError as jde:
            print(f"Excepción decodificando el mensaje: {jde}")
            return {"id":id_request,"estado": f"error:{jde} decoding"}
        
    except HTTPException as he:
        print(f"Excepcion HTTP consumiendo el mensaje: {he.detail}")
        return {"id":id_request,"estado": f"error:{he.detail} receiving, analysis has not started"}
    except asyncio.TimeoutError as te:
        print(f"Excepcion Timeout consumiendo el mensaje: {te}")
        return {"id":id_request, "estado": f"error:{te} timeout receiving, analysis has not started"}
    except Exception as e:
        print(f"Excepcion consumiendo el mensaje: {e}")
        return {"id":id_request, "estado": f"error:{e} receiving, analysis has not started"}
    finally:
        if rabbitmq is not None:
            await rabbitmq.close()

@route.post("/publicar_mensaje_respuesta/{id_request}", response_model=dict, tags=["RabbitMQ"] ,summary="Publicar mensaje de respuesta")
async def publicar_mensaje_respuesta(id_request:str,mensaje: dict = Body(...), current_user: str=Depends(get_current_user)):

    if id_request is None or len(id_request) == 0 or not is_valid_uuid(id_request):
        return {"id":"no puede ser nulo","estado": "Debe realizar una petición con un id de solicitud válido"}

    rabbitmq = None
    try:
        #print(f"Publicando mensaje: {mensaje}")
        if current_user is None:
            raise HTTPException(status_code=401, detail=f"usuario:{current_user}, no autorizado")
        #else:
        #    print(f"Usuario autenticado: {current_user}")
        rabbitmq = RabbitMQ()
        await rabbitmq.connect()
        id_request_respuesta = await rabbitmq.publish_message_response(id_request,mensaje)
        return {"id": id_request_respuesta,"estado": "análisis finalizado"}
    except Exception as e:
        print(f"Excepción publicando el mensaje:{e}")
        return {"id": None, "estado": f"error:{e}, sending de finished analysis"}
    finally:
        if rabbitmq is not None:
            await rabbitmq.close()

@route.get("/consumir_mensaje_respuesta/{id_request}", response_model=dict, tags=["RabbitMQ"] ,summary="Consumir mensaje de solicitud")
async def consumir_mensaje_respuesta(id_request: str, str=Depends(get_current_user)):
    if id_request is None or len(id_request) == 0 or not is_valid_uuid(id_request):
        return {"id":"no puede ser nulo","estado": "Debe realizar una petición con un id de solicitud válido"}

    mensaje_respuesta_future = asyncio.Future()
    rabbitmq = None
    try:
        rabbitmq = RabbitMQ()
        await rabbitmq.connect()

        async def callback(mensaje):
            if mensaje is not None and mensaje.body is not None and len(mensaje.body) > 0:
                print(f"Recibidos mensajes: {mensaje.body}")
                mensaje_respuesta_future.set_result(mensaje.body.decode("utf-8"))
            else:
                mensaje_respuesta_future.set_result("{}")

        await rabbitmq.consume_message_response(id_request,callback)
        mensaje_respuesta = await asyncio.wait_for(mensaje_respuesta_future, timeout=5) #espera 5 segundos
        if mensaje_respuesta is None:
            return {"id":id_request,"estado": "error, no se recibio ningun mensaje"}
        try:
            mensaje = json.loads(mensaje_respuesta)
            mensaje["estado"] = "resultado del análiis final recibido, cierre del proceso."
            return mensaje
        
        except json.JSONDecodeError as jde:
            print(f"Excepción decodificando el mensaje: {jde}")
            return {"id":id_request,"estado": f"{jde} decoding"}
        
    except HTTPException as he:
        print(f"Excepcion HTTP consumiendo el mensaje: {he.detail}")
        return {"id":id_request,"estado": f"error:{he.detail} receiving for end process"}
    except asyncio.TimeoutError as te:
        print(f"Excepcion Timeout consumiendo el mensaje: {te}")
        return {"id":id_request,"estado": f"error:{te} timeout receiving for end process"}
    except Exception as e:
        print(f"Excepcion consumiendo el mensaje: {e}")
        return {"id":id_request,"estado": f"error:{e}, receiving for end process"}
    finally:
        if rabbitmq is not None:
            await rabbitmq.close()
   


@route.get("/", response_class=RedirectResponse, status_code=302,include_in_schema=False)
async def redirect_to_docs():
    return "/docs"        