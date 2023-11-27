from api.routes import manageRoutes as RabbitMQRoutes
from fastapi import FastAPI

app = FastAPI()

app.include_router(RabbitMQRoutes.route)