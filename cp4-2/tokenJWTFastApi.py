from fastapi import FastAPI, Depends, HTTPException, status
import pydantic #pip install pydantic
 # pip install fastapi uvicorn[standard]
from fastapi.security import OAuth2PasswordBearer
import jwt #pip install PyJWT
from datetime import datetime, timedelta
from typing import Optional
from jwt import InvalidTokenError

#modelo de datos
class Token(pydantic.BaseModel):
    usuario: str
    clave: str

app = FastAPI()

# Configuración de secret key y algoritmo para JWT
SECRET_KEY = "mikeysecreta"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Función para generar un Token JWT
def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None):
    # 1. Crear una copia de los datos del usuario para el payload del token
    to_encode = data.copy()
    # 2. Calcular la fecha de expiración del token (si se proporciona)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        # Por defecto, expira en 15 minutos desde el momento actual
        expire = datetime.utcnow() + timedelta(minutes=15)
    # 3. Agregar la fecha de expiración al payload del token
    to_encode.update({"exp": expire})
    # 4. Codificar el token JWT utilizando PyJWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    # 5. Devolver el token JWT generado
    return encoded_jwt
    """
    Este token JWT luego se utiliza en la función login para autenticar 
    al usuario y se devuelve como parte de la respuesta en la ruta /token.
    """

# Función para obtener el token desde la solicitud HTTP
def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",headers={"WWW-Authenticate": "Bearer"})
    try:
        print("Inicio")
        # 1. Decodificar el token usando PyJWT y verificar la firma
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # 2. Obtener el nombre de usuario desde el payload
        username: str = payload.get("sub")
        # 3. Verificar si el nombre de usuario está presente en el payload
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:# 4. Manejar el caso en que el token ha expirado
        raise credentials_exception
    except InvalidTokenError:             # 5. Manejar el caso en que el token no es válido        
        raise credentials_exception
    # 6. Devolver el nombre de usuario si la validación ha sido exitosa
    return username

# Ruta para obtener un token
@app.post("/token")
#def login(username: str, password: str):
def login(token: Token):
    # Aquí deberías realizar la autenticación del usuario y verificar las credenciales
    # Por simplicidad, este ejemplo asume que el usuario y la contraseña son correctos
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    #access_token = create_jwt_token(data={"sub": token.get(username}, expires_delta=expires)
    access_token = create_jwt_token(data={"sub": token.usuario}, expires_delta=expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Ruta protegida que requiere un token válido
@app.get("/protected")
def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}! This is a protected route."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)

# curl -X POST "http://localhost:8100/token?username=billy&password=p455wr0d1234"
#    Respuesta:
#    {"access_token":"header.body.signature","token_type":"bearer"}
# Con el cambio del BaseModel deberá llamarse la ruta "/token" asi:
# curl -X POST "http://localhost:8000/token" -H "accept: application/json" -H "Content-Type: application/json" -d '{"usuario":"billy","clave":"p455wr0d1234"}'
# 
# curl -L -X GET "http://localhost:8100/protected/" -H "accept: application/json" -H "Authorization: Bearer Token<header.body.signature>", sin Token<> unicamnete el token 
#    Respuesta:
#    El {"message":"Hello, billy! This is a protected route."}
