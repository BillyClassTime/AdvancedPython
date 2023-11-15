from fastapi import Depends, FastAPI 
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

app = FastAPI()

@app.get("/private-route/")
def private_route(credentials: HTTPBasicCredentials = Depends(security)):
    # Validar las credenciales aquí
    return {"message": "Acceso autorizado"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

#curl -X GET "http://localhost:8000/private-route/" -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ="
#dXNlcm5hbWU6cGFzc3dvcmQ=" es la representación en Base64 de "username:password".