from fastapi import APIRouter,  Depends
from core.security import get_current_user

router=APIRouter()

@router.get("/clientes")
async def get_clients(current_user: dict = Depends(get_current_user)):
    # Aquí implementa la lógica para recuperar la lista de clientes
    # Solo llegará a este punto si el usuario está autenticado
    return {"message": "Lista de clientes"}
