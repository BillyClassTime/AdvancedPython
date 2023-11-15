from fastapi import FastAPI,Depends
from fastapi.security import OAuth2PasswordBearer

security = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

@app.get("/private-route/")
def private_route(token: str = Depends(security)):
    # Validar el token y realizar acciones seguras
    return {"message": "Acceso autorizado"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

#curl -X GET "http://localhost:8000/private-route/" -H "accept: application/json" -H "Authorization: Bearer <tu_token>"    