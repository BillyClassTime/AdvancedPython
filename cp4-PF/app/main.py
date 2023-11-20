from fastapi import FastAPI
from api.routes import login, clientes

app = FastAPI()

app.include_router(login.router)
app.include_router(clientes.router)