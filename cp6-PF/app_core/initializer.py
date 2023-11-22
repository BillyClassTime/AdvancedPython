from fastapi import FastAPI
from api.routes import serviceBusRoutes as azureservice

app = FastAPI()

app.include_router(azureservice.route)

