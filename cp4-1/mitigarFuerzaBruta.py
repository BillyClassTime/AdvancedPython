#py -m pip install --upgrade pip
#pip install fastapi uvicorn[standard] fastapi-limiter cachetools

import time
from fastapi import FastAPI, HTTPException, Depends, status, Body
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import hashlib
import secrets

app = FastAPI()

class Data(BaseModel):
    username: str
    password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Almacén para mantener un registro de intentos fallidos de inicio de sesión
# Para una API Resfull deberá usar una base de datos
failed_login_store = {}
# Almacén para mantener el estado de los tokens y usuarios autenticados
# Para una API Restfull deberá usar una base de datos
token_store = {}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Verificar si el token está presente y válido
    if token not in token_store:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token no válido")
    username = token_store[token]['username']
    # Obtener el número actual de intentos fallidos para esta cuenta
    failed_attempts_data = failed_login_store.get(username, {})
    failed_attempts = failed_attempts_data.get('attempts', 0)
    if failed_attempts >= 3:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, 
                            detail="Cuenta bloqueada. Por favor, inténtalo más tarde.")
    return {"username": username}

@app.post("/token")
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
        failed_login_store.setdefault(data.username, 
                                      {'password': hash_password(data.password), 
                                       'attempts': 0, 'timestamp': time.time()})
        failed_login_store[data.username]['attempts'] += 1
        if (failed_login_store[data.username]['attempts'] > 3 and 
                time.time() - failed_login_store[data.username]['timestamp'] < 60):
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, 
                                detail="Demasiados intentos fallidos. Por favor, inténtalo más tarde.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

@app.get("/clientes")
async def get_clients(current_user: dict = Depends(get_current_user)):
    # Aquí implementa la lógica para recuperar la lista de clientes
    # Solo llegará a este punto si el usuario está autenticado
    return {"message": "Lista de clientes"}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)