import jwt
from jwt import InvalidTokenError
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
import os
from custom_exceptions.customExceptions import customException

# Cargar la configuración de secret key y algoritmo para JWT
load_dotenv()
class SecurityConfig:
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

config = SecurityConfig()

# Configurar OAuth2
oatuh2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Función para generar un Token JWT
def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt

# Función para obtener el token desde la solicitud HTTP
def get_current_user(token: str = Depends(oatuh2_scheme)):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise customException("No se encontró el nombre de usuario")
    except jwt.ExpiredSignatureError:# 4. Manejar el caso en que el token ha expirado
        raise customException("El token ha expirado")
    except InvalidTokenError:             # 5. Manejar el caso en que el token no es válido        
        raise customException("El token no es válido")
    except Exception as e:
        raise customException("Error desconocido")
    return username