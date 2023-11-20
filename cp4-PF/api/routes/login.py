from fastapi import APIRouter,  HTTPException,status
from core.security import failed_login_store,hash_password,token_store
import secrets, time
from pydantic import BaseModel

router=APIRouter()

class Data(BaseModel):
    username: str
    password: str

@router.post("/token")
async def login(data: Data):
    stored_password = failed_login_store.get(data.username, {}).get('password')
    if stored_password and hash_password(data.password) == stored_password:
        # Generar un token único para el usuario
        token = secrets.token_hex(16)
        # Restablecer el contador de intentos fallidos al iniciar sesión exitosamente
        failed_login_store[data.username] = {'password': stored_password, 
                                             'attempts': 0, 'timestamp': time.time()}
        # Almacenar el token asociado al usuario
        token_store[token] = {'username': data.username}
        return {"access_token": token, "token_type": "bearer"}
    else:
        # Incrementar el contador de intentos fallidos
        print("Incrementar el contador de intentos fallidos")
        failed_login_store.setdefault(data.username, 
                                      {'password': hash_password(data.password), 
                                       'attempts': 0, 'timestamp': time.time()})
        failed_login_store[data.username]['attempts'] += 1
        if (failed_login_store[data.username]['attempts'] > 3 and 
                time.time() - failed_login_store[data.username]['timestamp'] < 60):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                                detail="Demasiados intentos fallidos. Por favor, inténtalo más tarde.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")
