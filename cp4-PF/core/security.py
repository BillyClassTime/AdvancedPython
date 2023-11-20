from fastapi import HTTPException, Depends,status
from fastapi.security import OAuth2PasswordBearer
import hashlib

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

failed_login_store = {}

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