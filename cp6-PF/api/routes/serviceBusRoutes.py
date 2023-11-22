from fastapi import APIRouter, HTTPException
from services.azureServicesBus import azureServicesBus

route = APIRouter()

@route.post("/enviar-mensaje/{cola_nombre}")
async def enviar_mensaje(cola_nombre: str, mensaje: str):
    try:
        asb = azureServicesBus()
        return await asb.enviar_mensaje_a_cola(mensaje, cola_nombre)    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@route.get("/recibir-mensaje/{cola_nombre}")
async def recibir_mensaje(cola_nombre: str):
    try:
        asb= azureServicesBus()
        return await asb.recibir_mensaje_de_cola(cola_nombre)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
