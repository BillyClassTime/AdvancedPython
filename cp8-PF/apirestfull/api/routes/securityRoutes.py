from datetime import timedelta
from fastapi import APIRouter
from services.securityServices import create_jwt_token,config

router = APIRouter()

@router.post("/token")
def login(username: str, password: str):
    # Aquí deberías realizar la autenticación del usuario y verificar las credenciales
    # Por simplicidad, este ejemplo asume que el usuario y la contraseña son correctos
    expires = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(data={"sub": username}, expires_delta=expires)
    return {"access_token": access_token, "token_type": "bearer"}