import datetime
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt #pip install python-jose

app = FastAPI()

# Configuración del token
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 2

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Función para generar un token JWT
def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Función para decodificar y verificar un token JWT
def decode_jwt_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exception

# Ruta protegida que requiere un token JWT válido
@app.get("/private-route/")
async def private_route(token_data: dict = Depends(decode_jwt_token)):
    return {"message": "Acceso autorizado"}

#curl -X GET "http://localhost:8000/private-route/" -H "accept: application/json" -H "Authorization: Bearer <tu_token>"


if __name__ == "__main__":
    # Generar un token JWT para la prueba inicial
    test_token = create_jwt_token({"sub": "testuser"})
    print(f"Token generado para prueba inicial: {test_token}")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)